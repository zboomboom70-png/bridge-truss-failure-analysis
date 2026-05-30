"""
Bridge Truss Progressive Failure Analysis Generator
Time-Series FEA Dataset for Forensic Fracture Investigation

Author: Stacey Blakeney, Forensic Mechanical Engineer
Application: ParaView Materials Science / Failure Analysis
"""
import math
import os

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

# Time stepping
NUM_TIMESTEPS = 12
TIME_START = 0.0
TIME_END = 2.2  # seconds to failure
DT = (TIME_END - TIME_START) / (NUM_TIMESTEPS - 1)

# Truss geometry (simplified Warren truss section)
TRUSS_LENGTH = 200  # mm (section under analysis)
TRUSS_HEIGHT = 80   # mm
MEMBER_WIDTH = 12   # mm (I-beam flange width)
MEMBER_THICKNESS = 4  # mm (flange/web thickness)

# Grid resolution
nx, ny, nz = 60, 30, 50
spacing = 1.5  # mm
origin = (-45, -22, -37)

# Material: Structural Steel A36
MATERIAL = {
    'E': 200000,           # Young's modulus (MPa)
    'nu': 0.29,            # Poisson's ratio
    'yield_strength': 250, # Yield strength (MPa)
    'ultimate_strength': 400,  # Ultimate tensile (MPa)
    'fracture_toughness': 50,  # K_IC (MPa√m)
    'density': 7850        # kg/m³
}

# Loading scenario: Overload event
DESIGN_LOAD = 150000  # N (design capacity)
OVERLOAD_FACTOR = 2.8 # Factor causing failure
PEAK_LOAD = DESIGN_LOAD * OVERLOAD_FACTOR  # 420 kN

# Failure initiation point (fatigue crack location)
CRACK_ORIGIN = (25, -15, 0)  # Bottom chord, tension side
INITIAL_CRACK_SIZE = 2.0  # mm (pre-existing fatigue crack)

def truss_geometry(x, y, z):
    """
    Define Warren truss cross-section geometry.
    Returns: (member_type, in_structure)
    0=outside, 1=bottom_chord, 2=top_chord, 3=diagonal, 4=weld_zone
    """
    # Bottom chord (y < -10)
    if -18 < y < -8:
        # I-beam profile
        if abs(z) < MEMBER_WIDTH/2:
            if y > -12 or y < -14:  # Flanges
                return 1, True
            elif abs(z) < MEMBER_THICKNESS/2:  # Web
                return 1, True
    
    # Top chord (y > 10)
    if 8 < y < 18:
        if abs(z) < MEMBER_WIDTH/2:
            if y < 12 or y > 14:
                return 2, True
            elif abs(z) < MEMBER_THICKNESS/2:
                return 2, True
    
    # Diagonal members (connecting top and bottom)
    # Simplified as rectangular sections
    diag_spacing = 40  # mm between diagonals
    for i in range(-2, 3):
        diag_center_x = i * diag_spacing
        
        # Calculate if point is on diagonal
        # Diagonals go from bottom to top at angle
        if abs(x - diag_center_x) < 20:
            # Rising diagonal
            expected_y = -13 + (x - diag_center_x + 20) * (26/40)
            if abs(y - expected_y) < 4 and abs(z) < 3:
                return 3, True
            
            # Falling diagonal (alternating pattern)
            if i % 2 == 0:
                expected_y2 = 13 - (x - diag_center_x + 20) * (26/40)
                if abs(y - expected_y2) < 4 and abs(z) < 3:
                    return 3, True
    
    # Weld zones (at connections)
    for i in range(-2, 3):
        node_x = i * diag_spacing
        # Bottom node
        if distance_2d(x, y, node_x, -13) < 6 and abs(z) < 8:
            return 4, True
        # Top node
        if distance_2d(x, y, node_x, 13) < 6 and abs(z) < 8:
            return 4, True
    
    return 0, False

def distance_2d(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def distance_3d(x, y, z, cx, cy, cz):
    return math.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2)

def crack_growth_model(time_fraction, x, y, z):
    """
    Paris law crack growth simulation.
    Returns: (crack_present, crack_length, crack_opening)
    """
    # Distance from crack origin
    dist = distance_3d(x, y, z, *CRACK_ORIGIN)
    
    # Crack grows exponentially with time (simplified Paris law)
    # da/dN = C * (ΔK)^m
    if time_fraction < 0.3:
        crack_radius = INITIAL_CRACK_SIZE * (1 + time_fraction * 2)
    elif time_fraction < 0.7:
        crack_radius = INITIAL_CRACK_SIZE * (1.6 + (time_fraction - 0.3) * 8)
    else:
        # Rapid unstable growth
        crack_radius = INITIAL_CRACK_SIZE * (4.8 + (time_fraction - 0.7) * 40)
    
    if dist < crack_radius:
        # Crack tip intensity
        if dist > crack_radius * 0.8:
            crack_intensity = 1.0  # At crack tip
        else:
            crack_intensity = 0.5 + 0.5 * (dist / crack_radius)
        
        # Crack opening displacement
        cod = 0.1 * crack_radius * (1 - dist/crack_radius) * time_fraction
        
        return True, crack_radius, cod, crack_intensity
    
    return False, 0, 0, 0

def calculate_stress_field(x, y, z, time_fraction, member_type):
    """
    Calculate stress distribution with crack singularity.
    Returns stress tensor components and derived quantities.
    """
    if member_type == 0:
        return {k: 0 for k in ['sigma_xx', 'sigma_yy', 'sigma_zz', 
                               'tau_xy', 'tau_yz', 'tau_xz',
                               'von_mises', 'principal_1', 'principal_3',
                               'triaxiality', 'plastic_strain']}
    
    # Base loading (increases with time)
    load_factor = 0.3 + 0.7 * time_fraction  # Ramp from 30% to 100%
    current_load = PEAK_LOAD * load_factor
    
    # Nominal stress in bottom chord (tension)
    area_chord = 2 * MEMBER_WIDTH * MEMBER_THICKNESS + (TRUSS_HEIGHT/4) * MEMBER_THICKNESS
    nominal_stress = current_load / area_chord
    
    # Member-specific stress
    if member_type == 1:  # Bottom chord (tension)
        base_sigma_xx = nominal_stress * 1.2
    elif member_type == 2:  # Top chord (compression)
        base_sigma_xx = -nominal_stress * 1.1
    elif member_type == 3:  # Diagonal
        base_sigma_xx = nominal_stress * 0.8 * (1 if y > 0 else -1)
    elif member_type == 4:  # Weld zone (stress concentration)
        base_sigma_xx = nominal_stress * 1.8  # SCF = 1.8
    else:
        base_sigma_xx = 0
    
    # Crack singularity (K-field)
    dist_crack = distance_3d(x, y, z, *CRACK_ORIGIN)
    crack_present, crack_len, cod, crack_intensity = crack_growth_model(time_fraction, x, y, z)
    
    if crack_present and dist_crack > 0.1:
        # Stress intensity factor K = σ√(πa) * Y
        K_I = base_sigma_xx * math.sqrt(math.pi * crack_len / 1000) * 1.12
        
        # Singular stress field near crack tip
        # σ = K / √(2πr)
        r = max(dist_crack - crack_len * 0.8, 0.5)
        singular_factor = K_I / math.sqrt(2 * math.pi * r / 1000)
        
        sigma_xx = base_sigma_xx + singular_factor * crack_intensity
        
        # Check for fracture (K_I > K_IC)
        if K_I > MATERIAL['fracture_toughness']:
            sigma_xx = MATERIAL['ultimate_strength'] * 1.5  # Beyond failure
    else:
        sigma_xx = base_sigma_xx
    
    # Other stress components
    sigma_yy = -0.1 * abs(sigma_xx)  # Transverse constraint
    sigma_zz = -0.05 * abs(sigma_xx)
    tau_xy = 0.15 * sigma_xx * math.sin(2 * math.atan2(y, x + 0.01))
    tau_yz = 0.05 * sigma_xx
    tau_xz = 0.08 * sigma_xx
    
    # von Mises stress
    von_mises = math.sqrt(0.5 * ((sigma_xx - sigma_yy)**2 + 
                                  (sigma_yy - sigma_zz)**2 + 
                                  (sigma_zz - sigma_xx)**2 +
                                  6 * (tau_xy**2 + tau_yz**2 + tau_xz**2)))
    
    # Principal stresses (simplified)
    I1 = sigma_xx + sigma_yy + sigma_zz
    principal_1 = sigma_xx * 1.1 if sigma_xx > 0 else sigma_xx * 0.9
    principal_3 = sigma_zz * 1.1 if sigma_zz < 0 else sigma_zz * 0.9
    
    # Stress triaxiality (important for ductile fracture)
    hydrostatic = I1 / 3
    triaxiality = hydrostatic / max(von_mises, 0.1)
    
    # Plastic strain (above yield)
    if von_mises > MATERIAL['yield_strength']:
        plastic_strain = (von_mises - MATERIAL['yield_strength']) / MATERIAL['E'] * 100
    else:
        plastic_strain = 0
    
    return {
        'sigma_xx': sigma_xx,
        'sigma_yy': sigma_yy,
        'sigma_zz': sigma_zz,
        'tau_xy': tau_xy,
        'tau_yz': tau_yz,
        'tau_xz': tau_xz,
        'von_mises': von_mises,
        'principal_1': principal_1,
        'principal_3': principal_3,
        'triaxiality': triaxiality,
        'plastic_strain': plastic_strain
    }

def calculate_displacement(x, y, z, time_fraction, stresses, member_type):
    """Calculate nodal displacements."""
    if member_type == 0:
        return (0, 0, 0)
    
    E = MATERIAL['E']
    
    # Elastic strain
    strain_xx = stresses['sigma_xx'] / E
    strain_yy = stresses['sigma_yy'] / E - 0.3 * strain_xx
    strain_zz = stresses['sigma_zz'] / E - 0.3 * strain_xx
    
    # Integrate strain to displacement (simplified)
    ux = strain_xx * (x - origin[0]) * 0.1
    uy = strain_yy * (y - origin[1]) * 0.1
    uz = strain_zz * (z - origin[2]) * 0.1
    
    # Add crack opening
    crack_present, crack_len, cod, _ = crack_growth_model(time_fraction, x, y, z)
    if crack_present and y < CRACK_ORIGIN[1]:
        uy -= cod * 2  # Opening in y-direction
    
    return (ux, uy, uz)

def generate_debris_particles(time_fraction):
    """
    Generate debris particles for failed material.
    Returns list of (x, y, z, vx, vy, vz, mass) tuples.
    """
    particles = []
    
    if time_fraction < 0.6:
        return particles  # No debris yet
    
    # Number of particles increases with failure progression
    n_particles = int((time_fraction - 0.6) * 200)
    
    for i in range(n_particles):
        # Particles originate from crack region
        px = CRACK_ORIGIN[0] + (hash(str(i) + "x") % 20 - 10)
        py = CRACK_ORIGIN[1] + (hash(str(i) + "y") % 10 - 5)
        pz = CRACK_ORIGIN[2] + (hash(str(i) + "z") % 15 - 7)
        
        # Velocity (ejected from fracture surface)
        speed = 5 + (hash(str(i) + "v") % 20)  # m/s
        vx = speed * 0.3 * (1 if hash(str(i)) % 2 == 0 else -1)
        vy = -speed * 0.8  # Primarily downward
        vz = speed * 0.2 * (hash(str(i) + "vz") % 3 - 1)
        
        # Mass (small fragments)
        mass = 0.001 + (hash(str(i) + "m") % 100) / 10000  # kg
        
        particles.append((px, py, pz, vx, vy, vz, mass))
    
    return particles

def write_vtk_timestep(filename, data, time_value, title):
    """Write VTK file for single timestep."""
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write(f"{title} | Time = {time_value:.3f} s\n")
        f.write("ASCII\nDATASET STRUCTURED_POINTS\n")
        f.write(f"DIMENSIONS {nx} {ny} {nz}\n")
        f.write(f"ORIGIN {origin[0]} {origin[1]} {origin[2]}\n")
        f.write(f"SPACING {spacing} {spacing} {spacing}\n")
        f.write(f"POINT_DATA {nx*ny*nz}\n")
        
        for name, values in data.items():
            if name == "Displacement":
                f.write(f"VECTORS {name} float\n")
                for v in values:
                    f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            else:
                f.write(f"SCALARS {name} float\nLOOKUP_TABLE default\n")
                for v in values:
                    f.write(f"{v:.6f}\n")

def write_particles_vtk(filename, particles, time_value):
    """Write debris particles as VTK polydata."""
    if not particles:
        # Write empty file
        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write(f"Debris Particles | Time = {time_value:.3f} s\n")
            f.write("ASCII\nDATASET POLYDATA\n")
            f.write("POINTS 0 float\n")
        return
    
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write(f"Debris Particles | Time = {time_value:.3f} s\n")
        f.write("ASCII\nDATASET POLYDATA\n")
        f.write(f"POINTS {len(particles)} float\n")
        
        for p in particles:
            f.write(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")
        
        f.write(f"\nVERTICES {len(particles)} {len(particles)*2}\n")
        for i in range(len(particles)):
            f.write(f"1 {i}\n")
        
        f.write(f"\nPOINT_DATA {len(particles)}\n")
        
        # Velocity vectors
        f.write("VECTORS Velocity float\n")
        for p in particles:
            f.write(f"{p[3]:.4f} {p[4]:.4f} {p[5]:.4f}\n")
        
        # Mass
        f.write("SCALARS Mass float\nLOOKUP_TABLE default\n")
        for p in particles:
            f.write(f"{p[6]:.6f}\n")
        
        # Particle ID
        f.write("SCALARS ParticleID int\nLOOKUP_TABLE default\n")
        for i in range(len(particles)):
            f.write(f"{i}\n")

# ============================================================================
# MAIN GENERATION LOOP
# ============================================================================

print("="*65)
print("BRIDGE TRUSS PROGRESSIVE FAILURE ANALYSIS")
print("Forensic Mechanical Failure Investigation")
print("="*65)
print(f"\nMaterial: Structural Steel A36")
print(f"Yield Strength: {MATERIAL['yield_strength']} MPa")
print(f"Ultimate Strength: {MATERIAL['ultimate_strength']} MPa")
print(f"Peak Load: {PEAK_LOAD/1000:.0f} kN ({OVERLOAD_FACTOR}x design)")
print(f"\nGenerating {NUM_TIMESTEPS} timesteps...")

yield_exceeded_timestep = None
yield_exceeded_node = None
yield_exceeded_location = None

for t_idx in range(NUM_TIMESTEPS):
    time_value = TIME_START + t_idx * DT
    time_fraction = t_idx / (NUM_TIMESTEPS - 1)
    
    print(f"\n  Timestep {t_idx}: t = {time_value:.3f} s ({time_fraction*100:.0f}% load)")
    
    data = {
        "member_type": [], "von_mises_stress": [], "yield_ratio": [],
        "plastic_strain": [], "triaxiality": [], "crack_damage": [],
        "sigma_xx": [], "principal_1": [], "principal_3": [],
        "Displacement": []
    }
    
    first_yield_this_step = None
    
    for k in range(nz):
        z = origin[2] + k * spacing
        for j in range(ny):
            y = origin[1] + j * spacing
            for i in range(nx):
                x = origin[0] + i * spacing
                
                member, in_struct = truss_geometry(x, y, z)
                
                if in_struct:
                    stresses = calculate_stress_field(x, y, z, time_fraction, member)
                    disp = calculate_displacement(x, y, z, time_fraction, stresses, member)
                    
                    vm = stresses['von_mises']
                    yield_ratio = vm / MATERIAL['yield_strength']
                    
                    # Track first yield exceedance
                    if yield_ratio > 1.0 and yield_exceeded_timestep is None:
                        yield_exceeded_timestep = t_idx
                        yield_exceeded_node = i + j * nx + k * nx * ny
                        yield_exceeded_location = (x, y, z)
                        first_yield_this_step = (x, y, z, vm)
                    
                    # Crack damage parameter
                    crack_present, crack_len, cod, crack_int = crack_growth_model(time_fraction, x, y, z)
                    damage = crack_int if crack_present else 0
                    
                else:
                    vm, yield_ratio, damage = 0, 0, 0
                    stresses = {k: 0 for k in ['sigma_xx', 'principal_1', 'principal_3', 
                                               'plastic_strain', 'triaxiality']}
                    disp = (0, 0, 0)
                
                data["member_type"].append(member)
                data["von_mises_stress"].append(vm)
                data["yield_ratio"].append(yield_ratio)
                data["plastic_strain"].append(stresses['plastic_strain'])
                data["triaxiality"].append(stresses['triaxiality'])
                data["crack_damage"].append(damage)
                data["sigma_xx"].append(stresses['sigma_xx'])
                data["principal_1"].append(stresses['principal_1'])
                data["principal_3"].append(stresses['principal_3'])
                data["Displacement"].append(disp)
    
    # Write structure timestep
    filename = f"truss_failure_{t_idx:04d}.vtk"
    write_vtk_timestep(filename, data, time_value, "Bridge Truss Progressive Failure")
    print(f"    Created: {filename}")
    
    # Generate and write debris particles
    particles = generate_debris_particles(time_fraction)
    particle_file = f"debris_particles_{t_idx:04d}.vtk"
    write_particles_vtk(particle_file, particles, time_value)
    if particles:
        print(f"    Created: {particle_file} ({len(particles)} particles)")
    
    if first_yield_this_step:
        print(f"    ⚠ First yield exceeded at ({first_yield_this_step[0]:.1f}, {first_yield_this_step[1]:.1f}, {first_yield_this_step[2]:.1f})")
        print(f"      von Mises: {first_yield_this_step[3]:.1f} MPa")

# ============================================================================
# GENERATE PVD FILE (ParaView Time Series)
# ============================================================================

print("\nGenerating PVD time series file...")

pvd_content = '<?xml version="1.0"?>\n'
pvd_content += '<VTKFile type="Collection" version="0.1">\n'
pvd_content += '  <Collection>\n'

for t_idx in range(NUM_TIMESTEPS):
    time_value = TIME_START + t_idx * DT
    pvd_content += f'    <DataSet timestep="{time_value:.4f}" file="truss_failure_{t_idx:04d}.vtk"/>\n'

pvd_content += '  </Collection>\n'
pvd_content += '</VTKFile>\n'

with open("bridge_truss_failure.pvd", "w") as f:
    f.write(pvd_content)
print("  Created: bridge_truss_failure.pvd")

# Debris PVD
pvd_debris = '<?xml version="1.0"?>\n'
pvd_debris += '<VTKFile type="Collection" version="0.1">\n'
pvd_debris += '  <Collection>\n'

for t_idx in range(NUM_TIMESTEPS):
    time_value = TIME_START + t_idx * DT
    pvd_debris += f'    <DataSet timestep="{time_value:.4f}" file="debris_particles_{t_idx:04d}.vtk"/>\n'

pvd_debris += '  </Collection>\n'
pvd_debris += '</VTKFile>\n'

with open("debris_pathlines.pvd", "w") as f:
    f.write(pvd_debris)
print("  Created: debris_pathlines.pvd")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*65)
print("GENERATION COMPLETE")
print("="*65)
print(f"Grid: {nx} x {ny} x {nz} = {nx*ny*nz:,} points")
print(f"Timesteps: {NUM_TIMESTEPS} (t = {TIME_START:.1f} to {TIME_END:.1f} s)")
print(f"\nYield Strength First Exceeded:")
if yield_exceeded_timestep is not None:
    t_yield = TIME_START + yield_exceeded_timestep * DT
    print(f"  Timestep: {yield_exceeded_timestep} (t = {t_yield:.3f} s)")
    print(f"  Node ID: {yield_exceeded_node}")
    print(f"  Location: ({yield_exceeded_location[0]:.1f}, {yield_exceeded_location[1]:.1f}, {yield_exceeded_location[2]:.1f}) mm")
else:
    print("  Not exceeded in simulation range")
print(f"\nFiles Generated:")
print(f"  - bridge_truss_failure.pvd (Structure time series)")
print(f"  - debris_pathlines.pvd (Particle time series)")
print(f"  - {NUM_TIMESTEPS} structure VTK files")
print(f"  - {NUM_TIMESTEPS} particle VTK files")
