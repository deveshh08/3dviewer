"""
╔══════════════════════════════════════════════════════════════════╗
║  iPromo 3D Configurator — Pure Python GLB Generator             ║
║  NO BLENDER REQUIRED — just run from your terminal              ║
║                                                                  ║
║  HOW TO RUN (2 steps):                                           ║
║  1. pip install pygltflib numpy                                  ║
║  2. python generate_glb_no_blender.py                            ║
║                                                                  ║
║  Output: quarter_zip.glb in the current folder                   ║
║  Then move it to: frontend/public/models/quarter_zip.glb         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import struct
import json
import base64
import math
import os

# ─── We build the GLB manually using numpy arrays ─────────────────────────────
# This creates simple-but-correct geometry that Three.js renders well
# with the studio HDRI lighting from the React app.

OUTPUT_FILE = "quarter_zip.glb"

# ─── GEOMETRY BUILDER HELPERS ─────────────────────────────────────────────────

def cylinder(radius_x, radius_y, height, segments, z_offset=0, closed=True):
    """
    Returns (positions, normals, uvs, indices) as numpy arrays.
    radius_x / radius_y allow elliptical cross-sections.
    """
    verts, norms, uvs = [], [], []
    idxs = []

    for ring in range(2):
        z = z_offset + (ring * height) - height / 2
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = math.cos(angle) * radius_x
            y = math.sin(angle) * radius_y
            nx = math.cos(angle)
            ny = math.sin(angle)
            u = i / segments
            v = ring
            verts.append([x, z, y])
            norms.append([nx, 0, ny])
            uvs.append([u, v])

    for i in range(segments):
        a = i
        b = (i + 1) % segments
        c = i + segments
        d = (i + 1) % segments + segments
        idxs += [a, c, b, b, c, d]

    if closed:
        # Top cap
        top_center = len(verts)
        top_z = z_offset + height / 2
        verts.append([0, top_z, 0])
        norms.append([0, 1, 0])
        uvs.append([0.5, 0.5])
        top_ring_start = segments
        for i in range(segments):
            a = top_ring_start + i
            b = top_ring_start + (i + 1) % segments
            idxs += [top_center, a, b]

        # Bottom cap
        bot_center = len(verts)
        bot_z = z_offset - height / 2
        verts.append([0, bot_z, 0])
        norms.append([0, -1, 0])
        uvs.append([0.5, 0.5])
        bot_ring_start = 0
        for i in range(segments):
            a = bot_ring_start + i
            b = bot_ring_start + (i + 1) % segments
            idxs += [bot_center, b, a]

    return (
        np.array(verts,  dtype=np.float32),
        np.array(norms,  dtype=np.float32),
        np.array(uvs,    dtype=np.float32),
        np.array(idxs,   dtype=np.uint16)
    )


def box(w, h, d, cx=0, cy=0, cz=0):
    """Simple box mesh centered at (cx, cy, cz)."""
    x, y, z = w/2, h/2, d/2
    verts = np.array([
        [-x, -y, -z], [ x, -y, -z], [ x,  y, -z], [-x,  y, -z],
        [-x, -y,  z], [ x, -y,  z], [ x,  y,  z], [-x,  y,  z],
    ], dtype=np.float32) + np.array([cx, cy, cz])

    idxs = np.array([
        0,1,2, 0,2,3,  4,6,5, 4,7,6,
        0,4,5, 0,5,1,  2,6,7, 2,7,3,
        0,3,7, 0,7,4,  1,5,6, 1,6,2,
    ], dtype=np.uint16)

    # Simple normals (per-face flat)
    norms = np.zeros_like(verts)
    norms[4:] = [0, 0, 1]

    uvs = np.zeros((len(verts), 2), dtype=np.float32)

    return verts, norms, uvs, idxs


def plane_facing_z(w, h, cx=0, cy=0, cz=0):
    """Flat quad facing -Z (front of sweatshirt), used for logo plane."""
    hw, hh = w/2, h/2
    verts = np.array([
        [cx-hw, cy-hh, cz],
        [cx+hw, cy-hh, cz],
        [cx+hw, cy+hh, cz],
        [cx-hw, cy+hh, cz],
    ], dtype=np.float32)
    norms = np.array([[0,0,-1],[0,0,-1],[0,0,-1],[0,0,-1]], dtype=np.float32)
    uvs   = np.array([[0,0],[1,0],[1,1],[0,1]], dtype=np.float32)
    idxs  = np.array([0,1,2, 0,2,3], dtype=np.uint16)
    return verts, norms, uvs, idxs


def torus(major_r, minor_r, major_seg=24, minor_seg=10, z_offset=0):
    """Generates a torus (for the collar)."""
    verts, norms, uvs, idxs = [], [], [], []
    for i in range(major_seg):
        for j in range(minor_seg):
            u = i / major_seg
            v = j / minor_seg
            theta = 2 * math.pi * u
            phi   = 2 * math.pi * v

            cx = math.cos(theta) * major_r
            cy = math.sin(theta) * major_r

            x = (major_r + minor_r * math.cos(phi)) * math.cos(theta)
            z = (major_r + minor_r * math.cos(phi)) * math.sin(theta)
            y = minor_r * math.sin(phi) + z_offset

            nx = math.cos(phi) * math.cos(theta)
            nz = math.cos(phi) * math.sin(theta)
            ny = math.sin(phi)

            verts.append([x, y, z])
            norms.append([nx, ny, nz])
            uvs.append([u, v])

    for i in range(major_seg):
        for j in range(minor_seg):
            a = i * minor_seg + j
            b = ((i + 1) % major_seg) * minor_seg + j
            c = i * minor_seg + (j + 1) % minor_seg
            d = ((i + 1) % major_seg) * minor_seg + (j + 1) % minor_seg
            idxs += [a, b, c, b, d, c]

    return (
        np.array(verts, dtype=np.float32),
        np.array(norms, dtype=np.float32),
        np.array(uvs,   dtype=np.float32),
        np.array(idxs,  dtype=np.uint16),
    )


def rotate_y(verts, norms, angle_rad):
    """Rotate mesh around Y axis (tilts sleeves outward)."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float32)
    return verts @ R.T, norms @ R.T


def translate(verts, tx, ty, tz):
    return verts + np.array([tx, ty, tz], dtype=np.float32)


def merge(meshes):
    """Concatenate a list of (verts, norms, uvs, idxs) into one mesh."""
    all_v, all_n, all_u, all_i = [], [], [], []
    offset = 0
    for v, n, u, i in meshes:
        all_v.append(v)
        all_n.append(n)
        all_u.append(u)
        all_i.append(i + offset)
        offset += len(v)
    return (
        np.concatenate(all_v),
        np.concatenate(all_n),
        np.concatenate(all_u),
        np.concatenate(all_i),
    )


# ─── BUILD EACH PART ──────────────────────────────────────────────────────────
print("Building geometry…")

# Body (torso) — elliptical cylinder, slightly tapered at top
v_body, n_body, u_body, i_body = cylinder(0.50, 0.32, 1.30, 32, closed=False)
# Taper the top (shoulders)
mask_top = v_body[:, 1] > 0.45
v_body[mask_top, 0] *= 0.85
v_body[mask_top, 2] *= 0.85

body_mesh = (v_body, n_body, u_body, i_body)

# Collar (torus around neck)
v_col, n_col, u_col, i_col = torus(0.27, 0.055, major_seg=24, minor_seg=10, z_offset=0.73)
# Flatten to ellipse
v_col[:, 2] *= 0.65
collar_mesh = (v_col, n_col, u_col, i_col)

# Sleeves
def make_sleeve(side):
    v, n, u, i = cylinder(0.175, 0.155, 0.86, 16, closed=True)
    # Rotate to droop outward
    angle = 0.42 if side == 'left' else -0.42
    v, n = rotate_y(v, n, angle)
    v = translate(v, -0.62 if side == 'left' else 0.62, 0.13, 0)
    return v, n, u, i

sleeve_left  = make_sleeve('left')
sleeve_right = make_sleeve('right')

# Cuffs
def make_cuff(side):
    v, n, u, i = cylinder(0.183, 0.163, 0.13, 16, closed=True)
    angle = 0.42 if side == 'left' else -0.42
    v, n = rotate_y(v, n, angle)
    tx = -0.62 if side == 'left' else 0.62
    ty = 0.13 - math.sin(0.42) * 0.43
    # Move to end of sleeve
    v = translate(v, tx + (-0.32 if side=='left' else 0.32), ty - 0.05, 0)
    return v, n, u, i

cuff_left  = make_cuff('left')
cuff_right = make_cuff('right')

# Waistband
v_waist, n_waist, u_waist, i_waist = cylinder(0.525, 0.335, 0.115, 32, z_offset=-0.715, closed=True)
waist_mesh = (v_waist, n_waist, u_waist, i_waist)

# Zipper strip
v_zip, n_zip, u_zip, i_zip = box(0.022, 0.42, 0.008, cx=0, cy=0.52, cz=-0.372)
zipper_mesh = (v_zip, n_zip, u_zip, i_zip)

# Logo plane (LEFT CHEST — this is where your logo goes!)
v_logo, n_logo, u_logo, i_logo = plane_facing_z(0.22, 0.22, cx=-0.17, cy=0.24, cz=-0.372)
logo_mesh = (v_logo, n_logo, u_logo, i_logo)

print("✔ All parts built")

# ─── GROUP BY MATERIAL ────────────────────────────────────────────────────────
body_parts   = merge([body_mesh, collar_mesh, sleeve_left, sleeve_right])
cuffs_parts  = merge([cuff_left, cuff_right, waist_mesh])
zipper_parts = merge([zipper_mesh])
logo_parts   = (v_logo, n_logo, u_logo, i_logo)

# ─── GLB SERIALISER ───────────────────────────────────────────────────────────

def pack_buffer(v, n, u, i):
    """Pack numpy arrays into a binary buffer, return (blob, accessors_info)."""
    v_bytes = v.astype(np.float32).tobytes()
    n_bytes = n.astype(np.float32).tobytes()
    u_bytes = u.astype(np.float32).tobytes()
    i_bytes = i.astype(np.uint16).tobytes()

    buf = v_bytes + n_bytes + u_bytes + i_bytes
    pos  = 0
    info = {
        'positions': {'offset': pos, 'length': len(v_bytes), 'count': len(v)},
    }
    pos += len(v_bytes)
    info['normals']   = {'offset': pos, 'length': len(n_bytes), 'count': len(n)}
    pos += len(n_bytes)
    info['texcoords'] = {'offset': pos, 'length': len(u_bytes), 'count': len(u)}
    pos += len(u_bytes)
    info['indices']   = {'offset': pos, 'length': len(i_bytes), 'count': len(i)}

    return buf, info


def bbox(arr):
    return arr.min(axis=0).tolist(), arr.max(axis=0).tolist()


def build_glb(parts_list):
    """
    parts_list: list of (name, (v,n,u,i), color_rgba)
    Returns raw GLB bytes.
    """
    buffers_data = []
    buffer_views = []
    accessors    = []
    meshes       = []
    nodes        = []
    materials    = []

    total_offset = 0

    # ── Materials ──────────────────────────────────────────────────────────────
    mat_defs = {
        "Body":             {"baseColorFactor": [0.49, 0.81, 0.81, 1.0], "roughnessFactor": 0.88, "metallicFactor": 0.0},
        "Cuffs":            {"baseColorFactor": [0.38, 0.68, 0.68, 1.0], "roughnessFactor": 0.90, "metallicFactor": 0.0},
        "Zipper":           {"baseColorFactor": [0.22, 0.22, 0.22, 1.0], "roughnessFactor": 0.30, "metallicFactor": 0.80},
        "LogoPlane_Chest":  {"baseColorFactor": [1.00, 1.00, 1.00, 1.0], "roughnessFactor": 0.70, "metallicFactor": 0.0},
    }
    mat_index = {}
    for idx, (name, props) in enumerate(mat_defs.items()):
        materials.append({
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": props["baseColorFactor"],
                "metallicFactor":  props["metallicFactor"],
                "roughnessFactor": props["roughnessFactor"],
            },
            "doubleSided": True,
        })
        mat_index[name] = idx

    # ── Pack each part into the buffer ─────────────────────────────────────────
    raw_buffers = []
    for part_name, (v, n, u, i), mat_name in parts_list:
        buf, info = pack_buffer(v, n, u, i)
        raw_buffers.append(buf)

        bv_base = len(buffer_views)

        # BufferViews (4 per part: positions, normals, uvs, indices)
        for key in ['positions', 'normals', 'texcoords']:
            buffer_views.append({
                "buffer":     0,
                "byteOffset": total_offset + info[key]['offset'],
                "byteLength": info[key]['length'],
                "target":     34962,  # ARRAY_BUFFER
            })
        buffer_views.append({
            "buffer":     0,
            "byteOffset": total_offset + info['indices']['offset'],
            "byteLength": info['indices']['length'],
            "target":     34963,  # ELEMENT_ARRAY_BUFFER
        })

        total_offset += len(buf)

        # Accessors
        acc_base = len(accessors)
        vmin, vmax = bbox(v)
        accessors.append({
            "bufferView":    bv_base + 0,
            "componentType": 5126,  # FLOAT
            "count":         info['positions']['count'],
            "type":          "VEC3",
            "min":           vmin,
            "max":           vmax,
        })
        nmin, nmax = bbox(n)
        accessors.append({
            "bufferView":    bv_base + 1,
            "componentType": 5126,
            "count":         info['normals']['count'],
            "type":          "VEC3",
            "min":           nmin,
            "max":           nmax,
        })
        umin, umax = bbox(u)
        accessors.append({
            "bufferView":    bv_base + 2,
            "componentType": 5126,
            "count":         info['texcoords']['count'],
            "type":          "VEC2",
            "min":           umin,
            "max":           umax,
        })
        accessors.append({
            "bufferView":    bv_base + 3,
            "componentType": 5123,  # UNSIGNED_SHORT
            "count":         info['indices']['count'],
            "type":          "SCALAR",
            "min":           [int(i.min())],
            "max":           [int(i.max())],
        })

        # Mesh
        mesh_idx = len(meshes)
        meshes.append({
            "name": part_name,
            "primitives": [{
                "attributes": {
                    "POSITION":   acc_base + 0,
                    "NORMAL":     acc_base + 1,
                    "TEXCOORD_0": acc_base + 2,
                },
                "indices":  acc_base + 3,
                "material": mat_index[mat_name],
            }]
        })

        nodes.append({
            "name": part_name,
            "mesh": mesh_idx,
        })

    # ── Combine all raw bytes ──────────────────────────────────────────────────
    binary_blob = b''.join(raw_buffers)

    # Pad to 4-byte boundary
    pad = (4 - len(binary_blob) % 4) % 4
    binary_blob += b'\x00' * pad

    # ── Build JSON chunk ───────────────────────────────────────────────────────
    gltf_json = {
        "asset":  {"version": "2.0", "generator": "iPromo-Configurator-Gen"},
        "scene":  0,
        "scenes": [{"name": "SweatshirtScene", "nodes": list(range(len(nodes)))}],
        "nodes":  nodes,
        "meshes": meshes,
        "accessors":   accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(binary_blob)}],
        "materials":   materials,
    }
    json_bytes = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
    json_pad   = (4 - len(json_bytes) % 4) % 4
    json_bytes += b' ' * json_pad  # JSON chunk padded with spaces

    # ── GLB header + chunks ────────────────────────────────────────────────────
    # GLB = 12-byte header + JSON chunk + BIN chunk
    json_chunk_len = 8 + len(json_bytes)   # 4 length + 4 type + data
    bin_chunk_len  = 8 + len(binary_blob)  # 4 length + 4 type + data
    total_len      = 12 + json_chunk_len + bin_chunk_len

    glb  = struct.pack('<III', 0x46546C67, 2, total_len)   # magic, version, total
    glb += struct.pack('<II',  len(json_bytes), 0x4E4F534A) + json_bytes  # JSON chunk
    glb += struct.pack('<II',  len(binary_blob), 0x004E4942) + binary_blob  # BIN chunk

    return glb


# ─── ASSEMBLE AND EXPORT ──────────────────────────────────────────────────────
print("Building GLB…")

parts = [
    ("Body",            body_parts,   "Body"),
    ("Cuffs",           cuffs_parts,  "Cuffs"),
    ("Zipper",          zipper_parts, "Zipper"),
    ("LogoPlane_Chest", logo_parts,   "LogoPlane_Chest"),
]

glb_bytes = build_glb(parts)

with open(OUTPUT_FILE, 'wb') as f:
    f.write(glb_bytes)

print(f"\n{'═'*60}")
print(f"  ✅  GLB exported successfully!")
print(f"  📁  Saved to: {os.path.abspath(OUTPUT_FILE)}  ({len(glb_bytes):,} bytes)")
print(f"  ➡️   Next: copy it to frontend/public/models/quarter_zip.glb")
print(f"  💡  Tip: preview at https://gltf-viewer.donmccurdy.com")
print(f"{'═'*60}\n")
