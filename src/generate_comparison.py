import base64
import io
import os
import sys
from PIL import Image

# The HTML template with CSS/JS for the comparison UI
# Note: Curly braces are doubled {{ }} to escape them for .format()
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Comparison Tool (High Res)</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #111;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        .viewport {{
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            cursor: grab;
            background-color: #111;
            position: relative;
        }}

        .canvas-container {{
            position: absolute;
            transform-origin: 0 0;
            top: 0;
            left: 0;
        }}

        .image-layer {{
            position: absolute;
            top: 0;
            left: 0;
            display: block;
        }}

        #layer-bottom {{
            z-index: 1;
        }}

        #layer-top {{
            z-index: 2;
        }}

        /* Gizmo Styles */
        #gizmo {{
            position: absolute;
            z-index: 10;
            cursor: move;
            user-select: none;
            touch-action: none;
        }}

        .handle {{
            width: var(--handle-size, 256px);
            height: var(--handle-size, 256px);
            background: rgba(255, 255, 255, 0.2);
            border: calc(var(--handle-size, 256px) * 0.03) solid #fff;
            border-radius: 50%;
            box-shadow: 0 0 calc(var(--handle-size, 256px) * 0.15) rgba(0,0,0,0.9);
            position: absolute;
            transform: translate(-50%, -50%);
        }}

        .rotator {{
            width: var(--rotator-size, 128px);
            height: var(--rotator-size, 128px);
            background: #ffcc00;
            border: calc(var(--rotator-size, 128px) * 0.06) solid #fff;
            border-radius: 50%;
            position: absolute;
            transform: translate(-50%, calc(var(--rotator-dist, 400px) * -1));
            cursor: crosshair;
            box-shadow: 0 0 calc(var(--rotator-size, 128px) * 0.2) rgba(0,0,0,0.9);
        }}

        .line-preview {{
            position: absolute;
            width: var(--line-width, 8px);
            height: 80000px;
            background: #fff;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            box-shadow: 0 0 calc(var(--line-width, 8px) * 2) rgba(0,0,0,1), 0 0 calc(var(--line-width, 8px) * 0.25) rgba(0,0,0,1);
        }}

        .ui-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none;
            z-index: 100;
        }}

        .label {{
            position: absolute;
            bottom: 20px;
            padding: 10px 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            z-index: 20;
            font-size: 12px;
            max-width: 40%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        #label-a {{ left: 20px; }}
        #label-b {{ right: 20px; }}

        .instructions {{
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.7);
            color: #eee;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            z-index: 20;
            text-align: center;
        }}
    </style>
</head>
<body>

<div class="viewport" id="viewport">
    <div class="canvas-container" id="canvas">
        <img id="layer-bottom" class="image-layer" src="data:image/jpeg;base64,{img_b_base64}">
        <img id="layer-top" class="image-layer" src="data:image/jpeg;base64,{img_a_base64}">
        
        <div id="gizmo">
            <div class="line-preview" id="line"></div>
            <div class="handle" id="center-handle"></div>
            <div class="rotator" id="rotate-handle"></div>
        </div>
    </div>
</div>

<div class="ui-overlay">
    <div class="label" id="label-a">{name_a}</div>
    <div class="label" id="label-b">{name_b}</div>
    <div class="instructions">
        Drag Viewport to Pan • Mouse Wheel to Zoom<br>
        Drag Gizmo to Move Split • Drag Yellow Circle to Rotate
    </div>
</div>

<script>
    const labelA = document.getElementById('label-a');
    const labelB = document.getElementById('label-b');
    const nameA = "{name_a}";
    const nameB = "{name_b}";

    const canvas = document.getElementById('canvas');
    const viewport = document.getElementById('viewport');
    const layerTop = document.getElementById('layer-top');
    const layerBottom = document.getElementById('layer-bottom');
    const gizmo = document.getElementById('gizmo');
    const centerHandle = document.getElementById('center-handle');
    const rotateHandle = document.getElementById('rotate-handle');
    const line = document.getElementById('line');

    let scale = 1.0;
    let panX = 0;
    let panY = 0;

    // Gizmo state (in image coordinates)
    let gizmoX = 0;
    let gizmoY = 0;
    let gizmoAngle = 0; // 0 degrees = vertical split

    let isPanning = false;
    let isDraggingGizmo = false;
    let isRotatingGizmo = false;

    let startX, startY;

    function updateTransform() {{
        canvas.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
    }}

    function updateClip() {{
        gizmo.style.left = gizmoX + 'px';
        gizmo.style.top = gizmoY + 'px';
        // 0 degrees is vertical (default line orientation)
        line.style.transform = `translate(-50%, -50%) rotate(${{gizmoAngle}}deg)`;

        const w = layerBottom.naturalWidth;
        const h = layerBottom.naturalHeight;

        // rad=0 is vertical line (nx=1, ny=0)
        const rad = gizmoAngle * (Math.PI / 180);
        const nx = Math.cos(rad);
        const ny = Math.sin(rad);

        const corners = [{{x:0,y:0}}, {{x:w,y:0}}, {{x:w,y:h}}, {{x:0,y:h}}];
        const getSide = (px, py) => nx * (px - gizmoX) + ny * (py - gizmoY);
        
        let polyPoints = [];
        for (let i = 0; i < 4; i++) {{
            const p1 = corners[i];
            const p2 = corners[(i + 1) % 4];
            if (getSide(p1.x, p1.y) <= 0) polyPoints.push(`${{p1.x}}px ${{p1.y}}px`);
            
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const denom = nx * dx + ny * dy;
            if (Math.abs(denom) > 0.0001) {{
                const t = (nx * (gizmoX - p1.x) + ny * (gizmoY - p1.y)) / denom;
                if (t >= 0 && t <= 1) {{
                    polyPoints.push(`${{p1.x + t*dx}}px ${{p1.y + t*dy}}px`);
                }}
            }}
        }}
        layerTop.style.clipPath = `polygon(${{polyPoints.join(', ')}})`;

        // Update Labels based on orientation and flip state
        const displayAngle = ((gizmoAngle % 360) + 360) % 360;
        
        if (displayAngle === 0) {{
            labelA.textContent = `${{nameA}} (Left)`;
            labelB.textContent = `${{nameB}} (Right)`;
        }} else if (displayAngle === 180) {{
            labelA.textContent = `${{nameA}} (Right)`;
            labelB.textContent = `${{nameB}} (Left)`;
        }} else if (displayAngle === 90) {{
            labelA.textContent = `${{nameA}} (Top)`;
            labelB.textContent = `${{nameB}} (Bottom)`;
        }} else if (displayAngle === 270) {{
            labelA.textContent = `${{nameA}} (Bottom)`;
            labelB.textContent = `${{nameB}} (Top)`;
        }}
    }}

    function init() {{
        const w = layerBottom.naturalWidth;
        const h = layerBottom.naturalHeight;
        if (!w || !h) {{
            setTimeout(init, 50);
            return;
        }}

        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';
        
        // Dynamic Gizmo Scaling
        const baseDim = Math.max(w, h);
        const gScale = baseDim / 12288;
        
        const handleSize = Math.max(32, 256 * gScale);
        const rotatorSize = Math.max(16, 128 * gScale);
        const rotatorDist = Math.max(60, 400 * gScale);
        const lineWidth = Math.max(1, 8 * gScale);
        
        document.documentElement.style.setProperty('--handle-size', handleSize + 'px');
        document.documentElement.style.setProperty('--rotator-size', rotatorSize + 'px');
        document.documentElement.style.setProperty('--rotator-dist', rotatorDist + 'px');
        document.documentElement.style.setProperty('--line-width', lineWidth + 'px');

        gizmoX = w / 2;
        gizmoY = h / 2;
        gizmoAngle = 0; // Vertical split
        
        scale = Math.min(window.innerWidth / w, window.innerHeight / h) * 0.9;
        panX = (window.innerWidth - w * scale) / 2;
        panY = (window.innerHeight - h * scale) / 2;
        
        updateTransform();
        updateClip();
    }}

    layerBottom.onload = init;
    window.onload = init; // Backup for base64 which might already be loaded

    // Interaction
    viewport.onpointerdown = (e) => {{
        if (e.target === centerHandle || e.target === rotateHandle) return;
        isPanning = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        viewport.setPointerCapture(e.pointerId);
    }};

    centerHandle.onpointerdown = (e) => {{
        isDraggingGizmo = true;
        centerHandle.setPointerCapture(e.pointerId);
        e.stopPropagation();
    }};

    rotateHandle.onpointerdown = (e) => {{
        isRotatingGizmo = true;
        rotateHandle.setPointerCapture(e.pointerId);
        e.stopPropagation();
    }};

    window.onpointermove = (e) => {{
        if (isPanning) {{
            panX = e.clientX - startX;
            panY = e.clientY - startY;
            updateTransform();
        }} else if (isDraggingGizmo) {{
            const rect = canvas.getBoundingClientRect();
            gizmoX = (e.clientX - rect.left) / scale;
            gizmoY = (e.clientY - rect.top) / scale;
            updateClip();
        }} else if (isRotatingGizmo) {{
            const rect = canvas.getBoundingClientRect();
            const cx = rect.left + gizmoX * scale;
            const cy = rect.top + gizmoY * scale;
            const dx = e.clientX - cx;
            const dy = e.clientY - cy;

            let rawAngle = Math.atan2(dy, dx) * (180 / Math.PI) + 90;

            const snapInterval = 45;
            const snapThreshold = 4;
            const snapped = Math.round(rawAngle / snapInterval) * snapInterval;

            if (Math.abs(rawAngle - snapped) < snapThreshold) {{
                gizmoAngle = snapped;
            }} else {{
                gizmoAngle = rawAngle;
            }}
            updateClip();
        }}
    }};

    window.onpointerup = () => {{
        isPanning = isDraggingGizmo = isRotatingGizmo = false;
    }};

    viewport.onwheel = (e) => {{
        e.preventDefault();
        const delta = -e.deltaY;
        const factor = Math.pow(1.1, delta / 100);
        
        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) / scale;
        const mouseY = (e.clientY - rect.top) / scale;

        const oldScale = scale;
        scale *= factor;
        scale = Math.max(0.001, Math.min(100, scale));
        
        panX -= mouseX * (scale - oldScale);
        panY -= mouseY * (scale - oldScale);
        
        updateTransform();
    }};

    window.onresize = () => {{
        // Optional: Re-center on resize if you want, but might be annoying
        updateTransform();
        updateClip();
    }};
</script>

</body>
</html>
"""

def process_image(img_path, target_size=None, quality=90):
    print(f"Processing {{img_path}}...")
    try:
        Image.MAX_IMAGE_PIXELS = None
        img = Image.open(img_path)
        if target_size and img.size != target_size:
            print(f"  Scaling from {{img.size}} to {{target_size}}...")
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return b64
    except Exception as e:
        print(f"Error processing {{img_path}}: {{e}}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: py generate_comparison.py <img_a> <img_b> [output_file]")
        sys.exit(1)

    img_a_path = sys.argv[1]
    img_b_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else "compare.html"

    Image.MAX_IMAGE_PIXELS = None
    img_a_info = Image.open(img_a_path)
    img_b_info = Image.open(img_b_path)
    max_w = max(img_a_info.size[0], img_b_info.size[0])
    max_h = max(img_a_info.size[1], img_b_info.size[1])
    target_size = (max_w, max_h)

    img_a_b64 = process_image(img_a_path, target_size=target_size)
    img_b_b64 = process_image(img_b_path, target_size=target_size)

    print(f"Generating {{output_path}}...")
    html_content = HTML_TEMPLATE.format(
        img_a_base64=img_a_b64,
        img_b_base64=img_b_b64,
        name_a=os.path.basename(img_a_path),
        name_b=os.path.basename(img_b_path)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Done! Created {{output_path}}.")

if __name__ == "__main__":
    main()
