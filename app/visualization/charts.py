from pathlib import Path

import matplotlib.pyplot as plt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.repository import ModelStateSnapshot


def performance_management_chart(db: Session, output_path: Path) -> Path:
    snapshots = db.scalars(select(ModelStateSnapshot).order_by(ModelStateSnapshot.snapshot_date.asc())).all()
    dates = [s.snapshot_date for s in snapshots]
    fit = [s.fitness for s in snapshots]
    fat = [s.fatigue for s in snapshots]
    form = [s.form for s in snapshots]

    plt.figure(figsize=(10, 4))
    plt.plot(dates, fit, label="Fitness")
    plt.plot(dates, fat, label="Fatigue")
    plt.plot(dates, form, label="Form")
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    return output_path
