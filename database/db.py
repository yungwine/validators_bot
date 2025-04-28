import datetime
import time

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy import select, update, delete

from database.models import Base, UserModel, NodeModel, TriggeredAlert, AlertModel


class Database:
    def __init__(self, db_url: str):
        self.engine: AsyncEngine = create_async_engine(db_url)
        self.session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_user(self, user_id: int, username=None):
        async with self.session_maker() as session:
            user = await session.scalar(select(UserModel).filter(UserModel.user_id == user_id))
            if user:
                return user
            user = UserModel(
                user_id=user_id,
                username=username,
                date_joined=datetime.datetime.now(),
            )
            # await session.execute(insert(UserModel).values(
            #     user_id=user_id,
            #     username=username,
            #     name=name,
            # ))
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def add_user_with_alerts(self, user_id: int, username=None):
        from alerts.alert import ALERTS
        async with self.session_maker() as session:
            user = await session.scalar(select(UserModel).filter(UserModel.user_id == user_id))
            if user:
                return user
            user = UserModel(
                user_id=user_id,
                username=username,
                date_joined=datetime.datetime.now(),
            )
            session.add(user)
            for alert in ALERTS:
                alert_model = AlertModel(
                    user_id=user.user_id,
                    alert_type=alert.type,
                    enabled=True
                )
                session.add(alert_model)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user(self, user_id: int):
        async with self.session_maker() as session:
            user = await session.scalar(select(UserModel).filter(UserModel.user_id == user_id))
            return user

    async def get_user_state(self, user_id: int):
        return (await self.get_user(user_id)).state

    async def set_user_state(self, user_id: int, state: str):
        async with self.session_maker() as session:
            await session.execute(
                update(UserModel)
                .filter(UserModel.user_id == user_id)
                .values({'state': state})
            )
            await session.commit()

    async def get_user_nodes(self, user_id: int) -> list[NodeModel]:
        async with self.session_maker() as session:
            nodes = await session.scalars(
                select(NodeModel).filter(NodeModel.user_id == user_id)
            )
            return list(nodes.all())

    async def add_node(self, user_id: int, adnl: str, label: str = None) -> None:
        async with self.session_maker() as session:
            node = NodeModel(
                user_id=user_id,
                adnl=adnl,
                label=label
            )
            session.add(node)
            await session.commit()

    async def set_node_label(self, user_id: int, node_adnl: str, label: str) -> None:
        async with self.session_maker() as session:
            await session.execute(
                update(NodeModel)
                .filter(NodeModel.user_id == user_id, NodeModel.adnl == node_adnl)
                .values({'label': label})
            )
            await session.commit()

    async def get_node_by_id(self, node_id: int) -> NodeModel | None:
        async with self.session_maker() as session:
            node = await session.scalar(
                select(NodeModel).filter(NodeModel.id == node_id)
            )
            return node

    async def remove_node(self, node_id: int) -> None:
        async with self.session_maker() as session:
            await session.execute(delete(NodeModel).filter(NodeModel.id == node_id))
            await session.commit()

    async def get_triggered_alerts(self, user_id: int, alert_name: str) -> list[TriggeredAlert]:
        async with self.session_maker() as session:
            alerts = await session.scalars(
                select(TriggeredAlert).filter(TriggeredAlert.user_id == user_id, TriggeredAlert.alert_name == alert_name)
            )
            return list(alerts.all())

    async def add_triggered_alert(self, user_id, alert_name, timestamp: int = None) -> None:
        if timestamp is None:
            timestamp = int(time.time())
        async with self.session_maker() as session:
            triggered_alert = TriggeredAlert(
                user_id=user_id,
                alert_name=alert_name,
                timestamp=timestamp
            )
            session.add(triggered_alert)
            await session.commit()

    async def delete_triggered_alert(self, user_id: int, alert_name: str) -> None:
        async with self.session_maker() as session:
            await session.execute(delete(TriggeredAlert).filter(TriggeredAlert.alert_name == alert_name, TriggeredAlert.user_id == user_id))
            await session.commit()

    async def get_user_alerts(self, user_id: int):
        async with self.session_maker() as session:
            alerts = await session.scalars(
                select(AlertModel).filter(AlertModel.user_id == user_id)
            )
            return list(alerts.all())

    async def set_user_alert_enabled(self, user_id: int, alert_type: str, enabled: bool) -> None:
        async with self.session_maker() as session:
            await session.execute(
                update(AlertModel)
                .filter(AlertModel.user_id == user_id, AlertModel.alert_type == alert_type)
                .values({'enabled': enabled})
            )
            await session.commit()

    async def get_users_with_enabled_alert(self, alert_type: str, only_with_nodes: bool = True) -> list[UserModel]:
        async with (self.session_maker() as session):
            if only_with_nodes:
                query = select(UserModel).join(
                    AlertModel,
                    UserModel.user_id == AlertModel.user_id
                ).join(
                    NodeModel,
                    UserModel.user_id == NodeModel.user_id
                ).where(
                    AlertModel.alert_type == alert_type,
                    AlertModel.enabled == True
                ).distinct()
            else:
                query = select(UserModel).join(
                    AlertModel,
                    UserModel.user_id == AlertModel.user_id
                ).where(
                    AlertModel.alert_type == alert_type,
                    AlertModel.enabled == True
                )

            result = await session.scalars(query)
            return list(result.all())

    async def close(self):
        await self.engine.dispose()
