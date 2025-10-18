# Crear directorio de videos públicos
PUBLIC_VIDEOS_DIR = "/var/www/fastapi-image-generator/public/videos"
os.makedirs(PUBLIC_VIDEOS_DIR, exist_ok=True)


def _save_video_and_get_url(video_path: str) -> str:
    """Move video to public directory and return public URL."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"video_{timestamp}_{unique_id}.mp4"
    
    final_path = os.path.join(PUBLIC_VIDEOS_DIR, filename)
    
    # Move temp video to public directory
    import shutil
    shutil.move(video_path, final_path)
    
    return f"{BASE_URL}/public/videos/{filename}"


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
            from video_generator import get_audio_duration
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
