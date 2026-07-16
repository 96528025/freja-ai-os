from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import Feedback, FeedbackSignal


class FeedbackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def for_brief(self, brief_id: str) -> list[Feedback]:
        return list(self.session.scalars(select(Feedback).where(Feedback.brief_id == brief_id)))

    def all_item_feedback(self) -> list[Feedback]:
        return list(
            self.session.scalars(
                select(Feedback)
                .where(Feedback.asset_id.is_not(None), Feedback.signal.is_not(None))
                .order_by(Feedback.updated_at.desc())
            )
        )

    def all_satisfaction(self) -> list[Feedback]:
        return list(
            self.session.scalars(
                select(Feedback).where(
                    Feedback.asset_id.is_(None), Feedback.satisfaction.is_not(None)
                )
            )
        )

    def upsert_item(
        self,
        *,
        brief_id: str,
        asset_id: str,
        signal: FeedbackSignal,
        reason: str | None,
    ) -> Feedback:
        feedback = self.session.scalar(
            select(Feedback).where(
                Feedback.brief_id == brief_id, Feedback.asset_id == asset_id
            )
        )
        if feedback is None:
            feedback = Feedback(brief_id=brief_id, asset_id=asset_id)
            self.session.add(feedback)
        feedback.signal = signal
        feedback.reason = reason
        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def clear_item(self, *, brief_id: str, asset_id: str) -> None:
        feedback = self.session.scalar(
            select(Feedback).where(
                Feedback.brief_id == brief_id, Feedback.asset_id == asset_id
            )
        )
        if feedback is not None:
            self.session.delete(feedback)
            self.session.commit()

    def upsert_satisfaction(
        self, *, brief_id: str, satisfaction: int, note: str | None
    ) -> Feedback:
        feedback = self.session.scalar(
            select(Feedback).where(
                Feedback.brief_id == brief_id, Feedback.asset_id.is_(None)
            )
        )
        if feedback is None:
            feedback = Feedback(brief_id=brief_id)
            self.session.add(feedback)
        feedback.satisfaction = satisfaction
        feedback.note = note
        self.session.commit()
        self.session.refresh(feedback)
        return feedback
