from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Example: "My Docking Project"
    protein_filename = Column(String)  # Name of the uploaded protein file
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="project")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))

    ligand_smiles = Column(String)  # Formula in SMILES format
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result_affinity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="jobs")
