from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base

class WellMaster(Base):
    __tablename__ = 'well_master'
    
    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(String, unique=True, index=True, nullable=False)
    field_name = Column(String)
    kb_elevation = Column(Float)
    total_depth_tvd = Column(Float)
    # Using String for dates based on processed data (e.g., '2024-01-01'). 
    # This could be switched to Date or DateTime as necessary.
    spud_date = Column(String) 
    
    # PostGIS spatial column (Point, WGS84)
    surface_location = Column(Geometry(geometry_type='POINT', srid=4326))
    
    # Bi-directional relationships to related tables
    drilling_params = relationship("DrillingParam", back_populates="well", cascade="all, delete-orphan")
    well_logs = relationship("WellLog", back_populates="well", cascade="all, delete-orphan")
    synthetic_events = relationship("SyntheticEvent", back_populates="well", cascade="all, delete-orphan")


class DrillingParam(Base):
    __tablename__ = 'drilling_param'
    
    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(String, ForeignKey('well_master.well_id'), nullable=False, index=True)
    timestamp = Column(DateTime, index=True)
    depth_md = Column(Float)
    depth_tvd = Column(Float)
    rop = Column(Float)
    wob = Column(Float)
    rpm = Column(Float)
    torque = Column(Float)
    mud_weight = Column(Float)
    ecd = Column(Float)
    mse = Column(Float)
    d_xc = Column(Float)
    
    # Back-reference
    well = relationship("WellMaster", back_populates="drilling_params")


class WellLog(Base):
    __tablename__ = 'well_log'
    
    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(String, ForeignKey('well_master.well_id'), nullable=False, index=True)
    depth_tvd = Column(Float, index=True)
    gamma_ray = Column(Float)
    resistivity = Column(Float)
    sonic = Column(Float)
    density = Column(Float)
    formation_top = Column(String, index=True)
    
    # Back-reference
    well = relationship("WellMaster", back_populates="well_logs")


class SyntheticEvent(Base):
    __tablename__ = 'synthetic_event'
    
    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(String, ForeignKey('well_master.well_id'), nullable=False, index=True)
    depth_start_tvd = Column(Float)
    depth_end_tvd = Column(Float)
    formation = Column(String)
    event_type = Column(String, index=True)
    severity = Column(String)
    root_cause = Column(String)
    mitigation_applied = Column(String)
    npt_hours = Column(Float)
    
    # Fallback to standard Postgres Array since pgvector compilation failed
    embedding = Column(ARRAY(Float))
    
    # Back-reference
    well = relationship("WellMaster", back_populates="synthetic_events")
