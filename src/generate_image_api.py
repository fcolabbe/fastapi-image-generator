"""A small FastAPI application to generate a news-style composite image.

This module exposes a single API endpoint `/generate-image` that accepts
an image file along with the headline and a highlighted portion of that
headline. It returns a composite image where:

* The provided photo is used as the background.
* A vertical strip along the left edge displays a repeated watermark text
  (by default `diarioeldia.cl`).
* The supplied highlight text is rendered on its own line in a blue font.
* The remainder of the headline is wrapped across one or more lines,
  each rendered in black. Each line is drawn on its own white box, and
  the lengths of the boxes adjust to the length of the text.
* A logo is placed in the top-right corner; by default this module
  expects a file named ``El_Dia.png`` to reside in the same directory
  as this script. You can override it by uploading a separate logo.

The API returns the resulting image as a PNG.

Example usage (with curl):

  curl -X POST -F "headline=La rayuela se tomó Paihuano: clubes de la comuna y de Vicuña animaron cuadrangular" \\
       -F "highlight=La rayuela se tomó Paihuano:" \\
       -F "image=@/path/to/your/photo.jpg" \\
       http://localhost:8000/generate-image --output result.png

Note: This script relies on FastAPI and uvicorn for serving the API. To
run the server, execute this file directly:

  python generate_image_api.py

Then visit http://127.0.0.1:8000/docs for an interactive Swagger UI.
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from typing import Optional

import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

from src.imgeditor import create_composite_image
from src.videoeditor import make_pan_scan_video
# Importar configuración
from src.config import Config


config = Config()

app = FastAPI(title=config.APP_NAME, description=config.APP_DESCRIPTION)

def _save_video_and_get_url(video_path: str) -> str:
    """Move video to public directory and return public URL."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"video_{timestamp}_{unique_id}.mp4"
    
    final_path = os.path.join(config.PUBLIC_VIDEOS_DIR, filename)
    
    # Move temp video to public directory
    import shutil
    shutil.move(video_path, final_path)
    
    return f"{config.BASE_URL}/public/videos/{filename}"

def _save_image_and_get_url(image: Image.Image) -> str:
    """Save image to public directory and return public URL."""
    # Generar nombre único para la imagen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"generated_{timestamp}_{unique_id}.png"

    # Guardar imagen
    filepath = os.path.join(config.PUBLIC_IMAGES_DIR, filename)
    image.save(filepath, format="PNG")

    # Retornar URL pública
    return f"{config.BASE_URL}/public/images/{filename}"

@app.post(
    "/generate-image",
    responses={
        200: {"description": "The generated image URL and metadata."},
        400: {"description": "Bad request"},
    },
)
async def generate_image(
    headline: str = Form(..., description="Full headline to display."),
    highlight: str = Form(..., description="Substring of the headline to highlight."),
    image: Optional[UploadFile] = File(
        None, description="Base photograph (PNG/JPEG)."),
    image_url: Optional[str] = Form(
        None, description="URL of the base photograph."),
    logo: Optional[UploadFile] = File(
        None, description="Optional logo file to override the default."
    ),
    logo_url: Optional[str] = Form(
        None, description="Optional URL of a custom logo file."
    ),
    recorte: Optional[str] = Form(
        None,
        description="ROI for Instagram crop as 'x,y,w,h' (0..1), e.g., '0.14,0,0.72,1'",
    ),
):
    """Generate a composite image from user-supplied headline, highlight and photograph.

    This endpoint accepts multipart/form-data containing the headline,
    highlight, base image, and optionally a custom logo. It saves the
    generated image to a public directory and returns the public URL.

    Returns:
        JSON response containing the public URL of the generated image.
    """
    # Validate input lengths
    if (not (image_url or image)):
        raise HTTPException(status_code=400, detail="You must provide either a 'image' or a 'image_url'")
    if not headline:
        raise HTTPException(status_code=400, detail="headline is required")
    if not highlight:
        raise HTTPException(status_code=400, detail="highlight is required")
    
    # Read the uploaded base image
    try:
        if (image):
            image_data = await image.read()
        elif (image_url):
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
        
        base_img = Image.open(io.BytesIO(image_data)).convert("RGBA")
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not download image from URL: {exc}"
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read base image: {exc}")
    
    # Read the optional logo if provided
    logo_img: Optional[Image.Image] = None
    if (logo or logo_url):
        try:
            if (logo is not None):
                logo_data = await logo.read()
            elif (logo_url is not None):
                logo_response = requests.get(logo_url, timeout=30)
                logo_response.raise_for_status()
                logo_data

            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
        
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=400, detail=f"Could not download logo from URL: {exc}"
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Could not read logo image: {exc}"
            )

    # Generate the composite image (horizontal version)
    results = create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
        recorte=recorte,
    )

    # Save both images and get public URLs
    image_url_horizontal = _save_image_and_get_url(results["facebook"])
    image_url_instagram = _save_image_and_get_url(results["instagram"])

    # Return JSON response with both URLs
    return {
        "success": True,
        "images": {
            "horizontal": {
                "url": image_url_horizontal,
                "format": "original",
                "description": "Imagen horizontal para web/Facebook",
            },
            "instagram": {
                "url": image_url_instagram,
                "format": "4:5",
                "dimensions": "1080x1350",
                "description": "Imagen vertical optimizada para Instagram",
            },
        },
        "headline": headline,
        "highlight": highlight,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/generate-video-from-url", responses={
    200: {
        "description": "The generated video URL and metadata."
    },
    400: {"description": "Bad request"}
})
async def generate_video_from_url(
    headline: str = Form(..., description="Full headline to display."),
    highlight: str = Form(..., description="Substring of the headline to highlight."),
    image_url: str = Form(..., description="URL of the base photograph."),
    duration: float = Form(5.0, description="Video duration in seconds (default: 5.0)"),
    direction: str = Form("left-to-right", description="Pan direction: left-to-right, right-to-left, top-to-bottom, bottom-to-top, zoom-in, zoom-out, diagonal-tl-br, diagonal-tr-bl"),
    fps: int = Form(30, description="Frames per second (default: 30)"),
    audio: Optional[UploadFile] = File(None, description="Optional audio file (mp3, wav, etc.)"),
    keep_aspect: bool = Form(True, description="Keep original image aspect ratio (default: True)")
):
    """Generate a cinematic pan & scan video from image URL.
    
    This endpoint creates a 9:16 (1080x1920) video with:
    - Cinematic pan & scan effect on the image
    - Static text overlay with headline and highlight
    - Same styling as generated images
    - Various pan directions and zoom effects
    
    Returns:
        JSON response containing the public URL of the generated video.
    """
    # Validate inputs
    if not image_url:
        raise HTTPException(status_code=400, detail="video url is required")
    if not headline:
        raise HTTPException(status_code=400, detail="headline is required")
    if not highlight:
        raise HTTPException(status_code=400, detail="highlight is required")
    
    if duration < 1 or duration > 30:
        raise HTTPException(status_code=400, detail="duration must be between 1 and 30 seconds")
    
    valid_directions = [
        "left-to-right", "right-to-left", 
        "top-to-bottom", "bottom-to-top",
        "zoom-in", "zoom-out",
        "diagonal-tl-br", "diagonal-tr-bl"
    ]
    if direction not in valid_directions:
        raise HTTPException(status_code=400, detail=f"direction must be one of: {', '.join(valid_directions)}")
    
    # Download image
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Could not download image from URL: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process downloaded image: {exc}")
    
    # Process audio if provided
    audio_path = None
    actual_duration = duration
    if audio is not None:
        try:
            audio_data = await audio.read()
            audio_path = f"/tmp/audio_{uuid.uuid4()}{os.path.splitext(audio.filename)[1]}"
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Obtener duración del audio para ajustar el video
            from videoeditor import get_audio_duration
            audio_duration = get_audio_duration(audio_path)
            if audio_duration:
                actual_duration = audio_duration
                
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not process audio file: {exc}")
    
    # Generate video
    try:
        # Save to temp file first
        temp_path = f"/tmp/video_{uuid.uuid4()}.mp4"
        
        make_pan_scan_video(
            output_path=temp_path,
            image_input=base_img,
            headline=headline,
            highlight=highlight,
            duration=actual_duration,
            out_w=1080 if not keep_aspect else None,
            out_h=1920 if not keep_aspect else None,
            fps=fps,
            direction=direction,
            ease_in_out=True,
            audio_path=audio_path,
            keep_aspect=keep_aspect
        )
        
        # Clean up temp audio file if exists
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Get video dimensions before moving the file
        import subprocess
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                temp_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                w, h = result.stdout.strip().split(',')
                video_dimensions = f"{w}x{h}"
                aspect = f"{w}:{h}" if keep_aspect else "9:16"
            else:
                video_dimensions = "unknown"
                aspect = "unknown"
        except:
            video_dimensions = "unknown"
            aspect = "unknown"
        
        # Move to public directory and get URL
        video_url = _save_video_and_get_url(temp_path)
        
        return {
            "success": True,
            "video_url": video_url,
            "headline": headline,
            "highlight": highlight,
            "duration": actual_duration,
            "direction": direction,
            "fps": fps,
            "format": aspect,
            "dimensions": video_dimensions,
            "keep_aspect": keep_aspect,
            "has_audio": audio_path is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {exc}")




if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    # Run the app on localhost for manual testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
