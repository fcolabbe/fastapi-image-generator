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

from imgeditor import create_composite_image
# Importar configuración
from config import Config


config = Config()

app = FastAPI(title=config.APP_NAME, description=config.APP_DESCRIPTION)


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




if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    # Run the app on localhost for manual testing
    uvicorn.run(app, host="0.0.0.0", port=8000)

