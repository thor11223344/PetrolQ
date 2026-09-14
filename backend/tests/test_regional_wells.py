import pytest
from trajectory_calc import compute_realistic_trajectory

def test_regional_formation_tops():
    # Test Assam
    assam_traj = compute_realistic_trajectory("OIL-BAGHJAN-1", 3000)
    assam_tops = assam_traj['formation_tops']
    assert any("Tipam" in top["name"] for top in assam_tops)
    assert any("Barail" in top["name"] for top in assam_tops)

    # Test Rajasthan
    raj_traj = compute_realistic_trajectory("OIL-RAJ-BAGHEWALA-1", 3000)
    raj_tops = raj_traj['formation_tops']
    assert any("Pariwar" in top["name"] for top in raj_tops)
    assert any("Baisakhi" in top["name"] for top in raj_tops)

    # Test KG
    kg_traj = compute_realistic_trajectory("OIL-KG-DEEPWATER-1", 3000)
    kg_tops = kg_traj['formation_tops']
    assert any("Shallow Marine" in top["name"] for top in kg_tops)
    assert any("Godavari" in top["name"] for top in kg_tops)

    # Test Mizoram
    mz_traj = compute_realistic_trajectory("OIL-MZ-AIZAWL-1", 3000)
    mz_tops = mz_traj['formation_tops']
    assert any("Bokabil" in top["name"] for top in mz_tops)
    assert any("Bhuban" in top["name"] for top in mz_tops)

def test_new_regional_wells():
    # Test newly added wells for KG Deepwater
    kg2_traj = compute_realistic_trajectory("OIL-KG-DWN-98-2", 4500)
    assert len(kg2_traj['formation_tops']) > 0

    # Test newly added wells for Mizoram
    mz2_traj = compute_realistic_trajectory("OIL-MZ-MAMIT-1", 4200)
    assert len(mz2_traj['formation_tops']) > 0

    # Test newly added wells for Rajasthan
    raj2_traj = compute_realistic_trajectory("OIL-RAJ-TANOT-2", 3000)
    assert len(raj2_traj['formation_tops']) > 0

def test_trajectory_generation():
    traj = compute_realistic_trajectory("OIL-BAGHJAN-1", 3500)
    assert len(traj['trajectory']['md']) > 0
    assert len(traj['trajectory']['x']) == len(traj['trajectory']['md'])
    assert len(traj['trajectory']['y']) == len(traj['trajectory']['md'])
    assert len(traj['trajectory']['z']) == len(traj['trajectory']['md'])
