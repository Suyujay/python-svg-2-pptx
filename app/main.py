import sys
from fastapi import FastAPI, HTTPException, Body, Query, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import datetime
from surquest.fastapi.utils.route import Route  # custom routes for documentation and FavIcon


# Add if a folder exists a folder ../src to import paths
if os.path.exists("./src"):
    sys.path.append("./src")

from surquest.utils.svg2pptx import SVG2Pptx

app = FastAPI(title="SVG to PPTX API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# custom routes to documentation and favicon
app.add_api_route(path=F"/", endpoint=Route.get_documentation, include_in_schema=False)

@app.post("/sources/SVG/target/PPTX:convert", response_class=Response)
async def convert_svg_to_pptx(
    svg_content: str = Body(
        default=open("./app/codeflow.svg", "r").read() if os.path.exists("./app/codeflow.svg") else "",
        media_type="text/plain", 
        description="The SVG content to convert"
    ),
    filename: str = Query(
        default=f"my-slide.{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.pptx",
        description="The name of the output PPTX file"
        )
):
    """
    Converts SVG content to a PowerPoint presentation.
    """

    if not svg_content:
        raise HTTPException(status_code=400, detail="SVG content is required")

    try:
        # Create a temporary file for the PPTX
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp_path = tmp.name

        # Initialize converter
        converter = SVG2Pptx()
        
        # Convert SVG string to PPTX
        # Note: SVG2Pptx.convert handles both file paths and SVG strings
        converter.convert(
            svg_input=svg_content,
            output_path=tmp_path
        )

        # Read the generated file
        with open(tmp_path, "rb") as f:
            pptx_data = f.read()

        # Clean up temporary file
        os.remove(tmp_path)

        return Response(
            content=pptx_data,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "SVG to PPTX API is running. use POST /convert to transform SVG to PPTX."}
