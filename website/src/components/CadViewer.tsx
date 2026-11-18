// Interactive 3D CAD viewer (Three.js + binary STLs tessellated from the CadQuery STEP assemblies).
// Shows both the current v3 Split-Grip design and the v4 Jamar-style concept prototype,
// with orbit/zoom, exploded view, X-ray housing, squeeze deflection demo, and Jamar 5-position span adjustment.

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { toCreasedNormals } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { IconRefresh } from "./Icons";

export type CadDesignId = "v3" | "jamar";
export type ViewPreset = "iso" | "side" | "front" | "top";

interface PartMeta {
  id: string;
  label: string;
  role: string;
  color: string;
  file?: string;
  isShell?: boolean;
  explode: [number, number, number];
  squeezeDir?: [number, number, number];
}

interface DesignSpec {
  id: CadDesignId;
  name: string;
  badge: string;
  statusTag: string;
  statusTone: "ok" | "accent";
  summary: string;
  dimensions: string;
  center: [number, number, number];
  camDist: number;
  parts: PartMeta[];
}

const JAMAR_GAPS = [26, 36, 46, 56, 66] as const; // mm bar-to-bar gap (pos 1..5); STL exported at pos 2 (36 mm)

const DESIGNS: Record<CadDesignId, DesignSpec> = {
  v3: {
    id: "v3",
    name: "v3 Split-Grip (Current)",
    badge: "Built & reading · PETG",
    statusTag: "Active build",
    statusTone: "ok",
    summary:
      "Barrel handle split lengthwise by a 3 mm seam. The palm half and closed electronics base bolt to the bottom of the load cell; the finger half floats on the top end.",
    dimensions: "57 × 82 × 204 mm",
    center: [11, 0, 50],
    camDist: 470,
    parts: [
      {
        id: "palm",
        label: "Palm half + base",
        role: "Fixed half · holds load cell bottom & electronics bay",
        color: "#c5cad3",
        file: "/models/v3_palm.stl",
        isShell: true,
        explode: [-26, 0, 0],
      },
      {
        id: "finger",
        label: "Finger half",
        role: "Moving half · bolts to load cell top across 3 mm seam",
        color: "#3b424d",
        file: "/models/v3_finger.stl",
        isShell: true,
        explode: [38, 0, 14],
        squeezeDir: [-1, 0, 0],
      },
      {
        id: "cover",
        label: "Bottom cover",
        role: "Closes the 57 × 82 mm electronics & cable bay (4 × M3)",
        color: "#8d949e",
        file: "/models/v3_cover.stl",
        isShell: true,
        explode: [0, 0, -46],
      },
      {
        id: "cell",
        label: "CZL601 100 kg cell",
        role: "Single-point parallel beam · sole force path between halves",
        color: "#229e89",
        explode: [0, 0, 0],
      },
      {
        id: "electronics",
        label: "Nano + HX711",
        role: "Arduino Nano & 24-bit ADC inside the fixed base",
        color: "#2d6cdf",
        explode: [0, 0, -24],
      },
    ],
  },
  jamar: {
    id: "jamar",
    name: "v4 Jamar-Style (Print-Ready)",
    badge: "0 supports · 5-pos span",
    statusTag: "Print-ready",
    statusTone: "accent",
    summary:
      "Ergonomic clinical two-handle dynamometer engineered for flat-bed support-free PETG printing (max 36 mm Z-height). Features a 4-finger trigger, contoured palm bar with captive M5 nuts, and enclosed electronics + uncut cable pod.",
    dimensions: "202 × 67 × 211 mm",
    center: [-45, 7.5, 50],
    camDist: 525,
    parts: [
      {
        id: "frame",
        label: "Main C-frame + truss arms",
        role: "Fixed body · prints flat in 36 mm Z · holds cell, Nano & 5 lock holes",
        color: "#c5cad3",
        file: "/models/jamar_frame.stl",
        isShell: true,
        explode: [18, 0, 0],
      },
      {
        id: "palm_bar",
        label: "Ergonomic palm bar",
        role: "Convex palm arch · captive M5 hex nuts across 5 spans (26–66 mm gap)",
        color: "#9aa2ad",
        file: "/models/jamar_palm_bar.stl",
        isShell: true,
        explode: [-42, 0, 0],
      },
      {
        id: "finger_part",
        label: "4-finger sculpted trigger",
        role: "Moving handle · contoured scallops + swept bracket across 3.5 mm gap",
        color: "#3b424d",
        file: "/models/jamar_finger.stl",
        isShell: true,
        explode: [-22, 0, 26],
        squeezeDir: [1, 0, 0],
      },
      {
        id: "cover",
        label: "Right electronics + cable pod",
        role: "18.5 mm cable bay + coil well · 4 × M3 countersunk screws",
        color: "#4a515d",
        file: "/models/jamar_cover.stl",
        isShell: true,
        explode: [0, 44, 0],
      },
      {
        id: "guard",
        label: "Left load-cell guard",
        role: "Encloses cell flank across 3.2 mm bending air gap (4 × M3)",
        color: "#4a515d",
        file: "/models/jamar_guard.stl",
        isShell: true,
        explode: [0, -34, 0],
      },
      {
        id: "cell",
        label: "CZL601 100 kg cell",
        role: "Stands upright inside spine · sole force path between palm & fingers",
        color: "#229e89",
        explode: [0, 0, 0],
      },
      {
        id: "electronics",
        label: "Nano + HX711",
        role: "Arduino Nano & 24-bit ADC inside fixed bay · rear octagonal USB port",
        color: "#2d6cdf",
        explode: [0, 18, -22],
      },
    ],
  },
};

const stlBufferCache = new Map<string, Promise<ArrayBuffer>>();

async function loadStl(url: string): Promise<THREE.BufferGeometry> {
  let req = stlBufferCache.get(url);
  if (!req) {
    req = fetch(url).then((res) => {
      if (!res.ok) throw new Error(`Failed to fetch CAD mesh (${res.status}): ${url}`);
      return res.arrayBuffer();
    });
    stlBufferCache.set(url, req);
  }
  const buf = await req;
  const raw = new STLLoader().parse(buf);
  const geom = toCreasedNormals(raw, Math.PI / 4);
  raw.dispose();
  return geom;
}

/** Procedural CZL601 100 kg parallel-beam load cell (22 x 40 x 130 mm, x 0..22, y -20..20, z 0..130) with binocular cutout & cable stub. */
function buildLoadCellGroup(): THREE.Group {
  const group = new THREE.Group();
  // Cross-section in X-Z plane (x: 0..22, z: 0..130) extruded across y = -20..20
  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  shape.lineTo(22, 0);
  shape.lineTo(22, 130);
  shape.lineTo(0, 130);
  shape.closePath();

  // Binocular shear-web cutout through the middle (x: 4..18, z: 42..88)
  const hole = new THREE.Path();
  hole.moveTo(4.5, 42);
  hole.lineTo(17.5, 42);
  hole.lineTo(17.5, 58);
  hole.lineTo(13.5, 65);
  hole.lineTo(17.5, 72);
  hole.lineTo(17.5, 88);
  hole.lineTo(4.5, 88);
  hole.lineTo(4.5, 72);
  hole.lineTo(8.5, 65);
  hole.lineTo(4.5, 58);
  hole.closePath();
  shape.holes.push(hole);

  const cellGeom = new THREE.ExtrudeGeometry(shape, { depth: 40, bevelEnabled: false });
  // ExtrudeGeometry extrudes along +Z from 0..40; rotate so shape (X, Y) maps to CAD (X, Z) and extrude depth maps to CAD Y (-20..20)
  cellGeom.rotateX(Math.PI / 2);
  // After rotateX(+90°): old (x, y, z) -> (x, -z, y); so z in 0..40 becomes y in -40..0. Shift +20 in Y -> -20..20!
  // Wait: in modelGroup we keep CAD coordinates (X, Y, Z) before modelGroup.rotation.x = -Math.PI/2.
  // So inside modelGroup: X=x, Y=y, Z=z.
  // ExtrudeGeometry starts in XY plane (X=0..22, Y=0..130) extruded along Z=0..40.
  // Rotating X by +PI/2 sends (x, y, z) -> (x, -z, y), so Y goes 0..130 -> Z=0..130, Z goes 0..40 -> Y=-40..0.
  cellGeom.translate(0, 20, 0);
  cellGeom.computeVertexNormals();

  const cellMat = new THREE.MeshStandardMaterial({
    color: "#229e89",
    metalness: 0.35,
    roughness: 0.38,
  });
  const body = new THREE.Mesh(cellGeom, cellMat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // White potting silicone / strain gauge cover on the front/back of the cutout
  const potMat = new THREE.MeshStandardMaterial({ color: "#e8eceb", roughness: 0.6, metalness: 0.05 });
  const pot = new THREE.Mesh(new THREE.BoxGeometry(10, 40.4, 24), potMat);
  pot.position.set(11, 0, 65);
  group.add(pot);

  // Shielded cable stub leaving +y face (y=20, x=11, z=5.5) and turning down into the base
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(11, 20, 5.5),
    new THREE.Vector3(11, 25, 5.5),
    new THREE.Vector3(11, 32, 0),
    new THREE.Vector3(11, 34.5, -18),
  ]);
  const cableGeom = new THREE.TubeGeometry(curve, 18, 2.55, 12, false);
  const cableMat = new THREE.MeshStandardMaterial({ color: "#d96b1b", roughness: 0.45, metalness: 0.1 });
  group.add(new THREE.Mesh(cableGeom, cableMat));

  return group;
}

/** Procedural Arduino Nano + HX711 inside the active design's fixed electronics bay (exact CAD coordinates). */
function buildElectronicsGroup(design: CadDesignId): THREE.Group {
  const g = new THREE.Group();
  const nanoMat = new THREE.MeshStandardMaterial({ color: "#2d6cdf", roughness: 0.4, metalness: 0.2 });
  const usbMat = new THREE.MeshStandardMaterial({ color: "#aeb6c2", roughness: 0.25, metalness: 0.8 });
  const hxMat = new THREE.MeshStandardMaterial({ color: "#1d9a57", roughness: 0.45, metalness: 0.15 });

  if (design === "v3") {
    const nano = new THREE.Mesh(new THREE.BoxGeometry(44, 18.1, 3.2), nanoMat);
    nano.position.set(10, -22.2, -38.2);
    g.add(nano);

    const usb = new THREE.Mesh(new THREE.BoxGeometry(6, 7.8, 3.8), usbMat);
    usb.position.set(-11, -22.2, -35.5);
    g.add(usb);

    const hx = new THREE.Mesh(new THREE.BoxGeometry(24, 3.2, 16), hxMat);
    hx.position.set(11, -36.5, -6);
    g.add(hx);
  } else {
    // Jamar v4: Nano on -y bay rail along X, USB pointing +x rear window; HX711 above Nano along front bay
    const nano = new THREE.Mesh(new THREE.BoxGeometry(44, 3.2, 18.1), nanoMat);
    nano.position.set(20.2, -4.9, -33.0);
    g.add(nano);

    const usb = new THREE.Mesh(new THREE.BoxGeometry(6, 3.8, 7.8), usbMat);
    usb.position.set(41.2, -2.2, -33.0);
    g.add(usb);

    const hx = new THREE.Mesh(new THREE.BoxGeometry(4, 24, 16), hxMat);
    hx.position.set(-0.7, -2.0, -11.5);
    g.add(hx);
  }
  return g;
}

export interface CadViewerProps {
  variant?: "full" | "hero";
  design?: CadDesignId;
  onDesignChange?: (id: CadDesignId) => void;
}

export function CadViewer({ variant = "full", design: controlledDesign, onDesignChange }: CadViewerProps) {
  const isHero = variant === "hero";
  const hostRef = useRef<HTMLDivElement>(null);
  const [internalDesign, setInternalDesign] = useState<CadDesignId>("v3");
  const design = controlledDesign ?? internalDesign;
  const setDesign = (id: CadDesignId) => {
    if (controlledDesign === undefined) setInternalDesign(id);
    onDesignChange?.(id);
  };

  const [explode, setExplode] = useState(0); // 0..100
  const [xray, setXray] = useState(false);
  const [squeeze, setSqueeze] = useState(false);
  const [jamarPos, setJamarPos] = useState(1); // 0..4 (default position 2 = 36 mm gap)
  const [selectedPart, setSelectedPart] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [presetTick, setPresetTick] = useState<{ preset: ViewPreset; n: number; keepRotate?: boolean }>({
    preset: "iso",
    n: 0,
    keepRotate: true,
  });

  // Live animation / parameter refs read inside the Three.js loop without re-creating the WebGL context
  const stateRef = useRef({ design, explode, xray, squeeze, jamarPos, selectedPart });
  stateRef.current = { design, explode, xray, squeeze, jamarPos, selectedPart };

  const sceneRefs = useRef<{
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    parts: Map<string, { obj: THREE.Object3D; meta: PartMeta; basePos: THREE.Vector3; mats: THREE.MeshStandardMaterial[] }>;
    modelGroup: THREE.Group;
    grid: THREE.GridHelper;
  } | null>(null);

  const spec = DESIGNS[design];
  const activePart = spec.parts.find((p) => p.id === selectedPart) ?? null;

  // Apply camera preset scaled to viewport aspect so tall/wide housings never crop
  useEffect(() => {
    const r = sceneRefs.current;
    if (!r) return;
    const aspectScale = r.camera.aspect < 1.05 ? 1.08 / Math.max(r.camera.aspect, 0.55) : 1;
    const d = DESIGNS[design].camDist * aspectScale;
    const target = new THREE.Vector3(0, 0, 0);
    let pos: THREE.Vector3;
    switch (presetTick.preset) {
      case "front":
        pos = new THREE.Vector3(0, 12, d);
        break;
      case "side":
        pos = new THREE.Vector3(d, 10, 0);
        break;
      case "top":
        pos = new THREE.Vector3(0, d, 0.01);
        break;
      case "iso":
      default:
        pos =
          design === "v3"
            ? new THREE.Vector3(d * 0.62, d * 0.24, d * 0.74)
            : new THREE.Vector3(-d * 0.44, d * 0.28, d * 0.85);
        break;
    }
    if (!presetTick.keepRotate) r.controls.autoRotate = false;
    r.camera.position.copy(pos);
    r.controls.target.copy(target);
    r.controls.update();
  }, [design, presetTick]);

  // Build scene & WebGL renderer once per mount
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let disposed = false;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    } catch {
      setError("WebGL 3D view is unavailable in this browser.");
      setLoading(false);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    host.innerHTML = "";
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 1, 3500);

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 140;
    controls.maxDistance = 1100;
    controls.maxPolarAngle = Math.PI * 0.92;
    controls.autoRotate = isHero && !reducedMotion;
    controls.autoRotateSpeed = 1.0;

    // Bright studio lighting so dark charcoal PETG retains crisp form in dark & light themes
    const hemi = new THREE.HemisphereLight("#ffffff", "#667080", 1.35);
    scene.add(hemi);
    const key = new THREE.DirectionalLight("#fffaf2", 1.55);
    key.position.set(220, 320, 260);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.near = 50;
    key.shadow.camera.far = 950;
    key.shadow.camera.left = -180;
    key.shadow.camera.right = 180;
    key.shadow.camera.top = 180;
    key.shadow.camera.bottom = -180;
    scene.add(key);
    const fill = new THREE.DirectionalLight("#cfe0ff", 0.9);
    fill.position.set(-240, 140, -180);
    scene.add(fill);
    const rim = new THREE.DirectionalLight("#ffffff", 0.85);
    rim.position.set(0, -160, -260);
    scene.add(rim);

    // Subtle ground grid aligned cleanly below the centered model
    const grid = new THREE.GridHelper(300, 15, "#8a929e", "#8a929e");
    grid.position.y = -108;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.16;
    scene.add(grid);

    const worldPivot = new THREE.Group();
    // Map CAD Z-up -> Three.js Y-up
    worldPivot.rotation.x = -Math.PI / 2;
    scene.add(worldPivot);

    const modelGroup = new THREE.Group();
    worldPivot.add(modelGroup);

    const partsMap = new Map<string, { obj: THREE.Object3D; meta: PartMeta; basePos: THREE.Vector3; mats: THREE.MeshStandardMaterial[] }>();
    sceneRefs.current = { camera, controls, parts: partsMap, modelGroup, grid };

    const updateSize = () => {
      const w = host.clientWidth;
      const h = host.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    };
    updateSize();
    const ro = new ResizeObserver(updateSize);
    ro.observe(host);

    // Track visibility so scrolled-off canvases don't spin GPU frames needlessly
    let visible = true;
    const io = new IntersectionObserver(
      (entries) => {
        visible = entries[0]?.isIntersecting ?? true;
      },
      { threshold: 0.01 },
    );
    io.observe(host);

    // Pause auto-rotate as soon as the user grabs the model
    const onControlStart = () => {
      controls.autoRotate = false;
    };
    controls.addEventListener("start", onControlStart);

    // Raycaster for click-to-inspect part
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let downPt = { x: 0, y: 0 };
    const onDown = (e: PointerEvent) => {
      downPt = { x: e.clientX, y: e.clientY };
    };
    const onUp = (e: PointerEvent) => {
      if (Math.hypot(e.clientX - downPt.x, e.clientY - downPt.y) > 5) return;
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const targets: THREE.Object3D[] = [];
      for (const entry of partsMap.values()) targets.push(entry.obj);
      const hits = raycaster.intersectObjects(targets, true);
      if (hits.length === 0) {
        setSelectedPart(null);
        return;
      }
      let cur: THREE.Object3D | null = hits[0].object;
      while (cur && !cur.userData.partId) cur = cur.parent;
      const pid = cur?.userData.partId as string | undefined;
      if (pid) setSelectedPart((prev) => (prev === pid ? null : pid));
    };
    renderer.domElement.addEventListener("pointerdown", onDown);
    renderer.domElement.addEventListener("pointerup", onUp);

    let raf = 0;
    const t0 = performance.now();
    const animate = (now: number) => {
      if (disposed) return;
      raf = requestAnimationFrame(animate);
      if (!visible) return;

      const st = stateRef.current;
      const expFrac = st.explode / 100;
      const pulse = st.squeeze ? 0.5 - 0.5 * Math.cos(((now - t0) / 1000) * 3.1) : 0;

      for (const entry of partsMap.values()) {
        const { obj, meta, basePos, mats } = entry;
        let dx = meta.explode[0] * expFrac;
        let dy = meta.explode[1] * expFrac;
        let dz = meta.explode[2] * expFrac;

        if (st.design === "jamar" && meta.id === "palm_bar") {
          dx += JAMAR_GAPS[1] - JAMAR_GAPS[st.jamarPos];
        }
        if (meta.squeezeDir && pulse > 0) {
          // Visualise 1.6 mm deflection along the squeeze axis so the 3 mm isolation gap stays clear
          dx += meta.squeezeDir[0] * pulse * 1.6;
          dy += meta.squeezeDir[1] * pulse * 1.6;
          dz += meta.squeezeDir[2] * pulse * 1.6;
        }
        obj.position.set(basePos.x + dx, basePos.y + dy, basePos.z + dz);

        const isSel = st.selectedPart === meta.id;
        const dimOthers = st.selectedPart !== null && !isSel;
        for (const m of mats) {
          if (meta.isShell && st.xray) {
            m.transparent = true;
            m.opacity = dimOthers ? 0.12 : 0.24;
            m.depthWrite = false;
          } else if (dimOthers) {
            m.transparent = true;
            m.opacity = 0.28;
            m.depthWrite = true;
          } else {
            m.transparent = false;
            m.opacity = 1;
            m.depthWrite = true;
          }
          m.emissive.set(isSel ? "#2747f5" : "#000000");
          m.emissiveIntensity = isSel ? 0.25 : 0;
        }
      }

      controls.update();
      renderer.render(scene, camera);
    };
    raf = requestAnimationFrame(animate);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      controls.removeEventListener("start", onControlStart);
      renderer.domElement.removeEventListener("pointerdown", onDown);
      renderer.domElement.removeEventListener("pointerup", onUp);
      controls.dispose();
      grid.geometry.dispose();
      (grid.material as THREE.Material).dispose();
      renderer.dispose();
      sceneRefs.current = null;
    };
  }, [isHero]);

  // Load / swap meshes when `design` changes
  useEffect(() => {
    const r = sceneRefs.current;
    if (!r) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    setSelectedPart(null);

    const activeSpec = DESIGNS[design];
    const disposables: { dispose: () => void }[] = [];
    r.modelGroup.clear();
    r.parts.clear();
    // Center the CAD assembly on the origin (worldPivot rotates -90° around X)
    r.modelGroup.position.set(-activeSpec.center[0], -activeSpec.center[1], -activeSpec.center[2]);

    async function populate() {
      try {
        // Internal load cell (and electronics for v3)
        const cell = buildLoadCellGroup();
        cell.userData.partId = "cell";
        const cellMats: THREE.MeshStandardMaterial[] = [];
        cell.traverse((c) => {
          if ((c as THREE.Mesh).isMesh) {
            const mesh = c as THREE.Mesh;
            const m = mesh.material as THREE.MeshStandardMaterial;
            cellMats.push(m);
            disposables.push(mesh.geometry, m);
          }
        });
        const cellMeta = activeSpec.parts.find((p) => p.id === "cell")!;
        r!.modelGroup.add(cell);
        r!.parts.set("cell", { obj: cell, meta: cellMeta, basePos: cell.position.clone(), mats: cellMats });

        const elec = buildElectronicsGroup(design);
        elec.userData.partId = "electronics";
        const elecMats: THREE.MeshStandardMaterial[] = [];
        elec.traverse((c) => {
          if ((c as THREE.Mesh).isMesh) {
            const mesh = c as THREE.Mesh;
            const m = mesh.material as THREE.MeshStandardMaterial;
            elecMats.push(m);
            disposables.push(mesh.geometry, m);
          }
        });
        const elecMeta = activeSpec.parts.find((p) => p.id === "electronics")!;
        r!.modelGroup.add(elec);
        r!.parts.set("electronics", { obj: elec, meta: elecMeta, basePos: elec.position.clone(), mats: elecMats });

        // Load STL shells concurrently
        const fileParts = activeSpec.parts.filter((p) => p.file);
        const loaded = await Promise.all(
          fileParts.map(async (meta) => ({
            meta,
            geom: await loadStl(meta.file!),
          })),
        );
        if (cancelled) {
          for (const { geom } of loaded) geom.dispose();
          return;
        }

        for (const { meta, geom } of loaded) {
          const mat = new THREE.MeshStandardMaterial({
            color: meta.color,
            roughness: meta.id.includes("finger") ? 0.5 : 0.4,
            metalness: 0.08,
          });
          disposables.push(geom, mat);
          const mesh = new THREE.Mesh(geom, mat);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.userData.partId = meta.id;
          r!.modelGroup.add(mesh);
          r!.parts.set(meta.id, { obj: mesh, meta, basePos: mesh.position.clone(), mats: [mat] });
        }
        setLoading(false);
        setPresetTick((p) => ({ preset: "iso", n: p.n + 1, keepRotate: true }));
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load CAD meshes.");
          setLoading(false);
        }
      }
    }
    void populate();
    return () => {
      cancelled = true;
      for (const d of disposables) d.dispose();
    };
  }, [design]);

  const jamarGapMm = JAMAR_GAPS[jamarPos];
  const jamarOuterSpanMm = jamarGapMm + 20 + 24; // PB_T (20) + finger bar depth (24)

  const stageEl = (
    <div className="cad-stage">
      <div ref={hostRef} className="cad-canvas" aria-label={`Interactive 3D CAD model of ${spec.name}`} />

      {loading && (
        <div className="cad-overlay">
          <div className="spinner" aria-hidden="true" />
          <span className="muted small">Loading CAD geometry…</span>
        </div>
      )}
      {error && (
        <div className="cad-overlay">
          <p className="error-text">{error}</p>
        </div>
      )}

      <div className="cad-hud-top">
        <div className="cad-views" role="group" aria-label="Camera views">
          {(
            [
              ["iso", "3/4"],
              ["side", "Side"],
              ["front", "Front"],
              ["top", "Top"],
            ] as const
          ).map(([preset, label]) => (
            <button
              key={preset}
              type="button"
              className="cad-chip"
              onClick={() => setPresetTick((p) => ({ preset, n: p.n + 1 }))}
            >
              {label}
            </button>
          ))}
          <button
            type="button"
            className="cad-chip"
            onClick={() => {
              setExplode(0);
              setXray(false);
              setSqueeze(false);
              setSelectedPart(null);
              setPresetTick((p) => ({ preset: "iso", n: p.n + 1, keepRotate: isHero }));
            }}
            title="Reset view & assembly"
          >
            <IconRefresh size={13} /> Reset
          </button>
        </div>
      </div>

      <div className="cad-hud-bottom">
        <span className="muted small">
          {isHero ? "Drag to orbit · Scroll to zoom · Click part" : "Drag to orbit · Scroll to zoom · Click any part to inspect"}
        </span>
        {activePart && (
          <span className="tag accent">
            {activePart.label}: {activePart.role}
          </span>
        )}
      </div>
    </div>
  );

  if (isHero) {
    return (
      <div className="cad-hero-wrap">
        {stageEl}
        <div className="cad-hero-bar">
          <div className="cad-hero-bar-row">
            <label htmlFor="cad-hero-explode" className="small muted" style={{ whiteSpace: "nowrap" }}>
              Explode <b className="mono">{explode}%</b>
            </label>
            <input
              id="cad-hero-explode"
              type="range"
              min={0}
              max={100}
              value={explode}
              onChange={(e) => setExplode(Number(e.target.value))}
              className="cad-slider"
              aria-label="Explode assembly"
            />
            <button
              type="button"
              className={`cad-chip-btn${xray ? " active" : ""}`}
              aria-pressed={xray}
              onClick={() => setXray((v) => !v)}
            >
              X-ray
            </button>
            <button
              type="button"
              className={`cad-chip-btn${squeeze ? " active" : ""}`}
              aria-pressed={squeeze}
              onClick={() => setSqueeze((v) => !v)}
            >
              {squeeze ? "Squeezing" : "Squeeze"}
            </button>
          </div>
          {design === "jamar" && (
            <div className="cad-hero-bar-row">
              <span className="small muted">Jamar span:</span>
              <div className="pill-tabs" role="group" aria-label="Jamar handle position">
                {JAMAR_GAPS.map((gap, i) => (
                  <button
                    key={gap}
                    type="button"
                    className={`pill-tab${jamarPos === i ? " active" : ""}`}
                    onClick={() => setJamarPos(i)}
                    title={`Position ${i + 1}: ${gap} mm bar-to-bar gap`}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
              <span className="mono small muted">{jamarGapMm} mm gap</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card cad-shell">
      <div className="cad-head">
        <div style={{ display: "grid", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <span className="eyebrow">Interactive 3D CAD</span>
            <span className={`tag ${spec.statusTone}`}>{spec.statusTag}</span>
            <span className="tag mono">{spec.dimensions}</span>
          </div>
          <h3>{spec.name}</h3>
          <p className="muted small" style={{ maxWidth: "66ch" }}>
            {spec.summary}
          </p>
        </div>

        <div className="pill-tabs" role="tablist" aria-label="Choose CAD design">
          {(["v3", "jamar"] as CadDesignId[]).map((id) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={design === id}
              className={`pill-tab${design === id ? " active" : ""}`}
              onClick={() => setDesign(id)}
            >
              {id === "v3" ? "v3 Split-Grip (Current)" : "v4 Jamar-Style (Print-Ready)"}
            </button>
          ))}
        </div>
      </div>

      <div className="cad-body">
        {stageEl}

        <aside className="cad-controls">
          <div className="cad-control-group">
            <div className="cad-control-row">
              <label htmlFor="cad-explode">
                <b>Explode assembly</b>
              </label>
              <span className="mono small muted">{explode}%</span>
            </div>
            <input
              id="cad-explode"
              type="range"
              min={0}
              max={100}
              value={explode}
              onChange={(e) => setExplode(Number(e.target.value))}
              className="cad-slider"
            />
          </div>

          <div className="cad-toggles">
            <button
              type="button"
              className={`btn btn-sm ${xray ? "btn-primary" : "btn-secondary"}`}
              aria-pressed={xray}
              onClick={() => setXray((v) => !v)}
            >
              {xray ? "X-ray: on" : "X-ray housing"}
            </button>
            <button
              type="button"
              className={`btn btn-sm ${squeeze ? "btn-primary" : "btn-secondary"}`}
              aria-pressed={squeeze}
              onClick={() => setSqueeze((v) => !v)}
            >
              {squeeze ? "Squeezing…" : "Animate squeeze"}
            </button>
          </div>

          {design === "jamar" && (
            <div className="cad-control-group">
              <div className="cad-control-row">
                <span>
                  <b>Jamar span position</b>
                </span>
                <span className="mono small muted">
                  Pos {jamarPos + 1} · {jamarGapMm} mm gap ({jamarOuterSpanMm} mm outer)
                </span>
              </div>
              <div className="pill-tabs" style={{ width: "100%" }} role="group" aria-label="Jamar handle position">
                {JAMAR_GAPS.map((gap, i) => (
                  <button
                    key={gap}
                    type="button"
                    style={{ flex: 1 }}
                    className={`pill-tab${jamarPos === i ? " active" : ""}`}
                    onClick={() => setJamarPos(i)}
                    title={`Position ${i + 1}: ${gap} mm bar-to-bar gap`}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="cad-parts">
            <span className="eyebrow">Parts (click to isolate)</span>
            <ul>
              {spec.parts.map((p) => {
                const active = selectedPart === p.id;
                return (
                  <li key={p.id}>
                    <button
                      type="button"
                      className={`cad-part-btn${active ? " active" : ""}`}
                      onClick={() => setSelectedPart((prev) => (prev === p.id ? null : p.id))}
                    >
                      <span className="swatch" style={{ background: p.color }} aria-hidden="true" />
                      <span>
                        <b>{p.label}</b>
                        <small>{p.role}</small>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default CadViewer;
