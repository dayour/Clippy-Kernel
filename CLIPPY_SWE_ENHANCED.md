# Clippy SWE Agent - Enhanced OG Functionality

## New Document & Media Processing Features

Clippy SWE Agent now includes powerful document and media processing capabilities, including PowerPoint generation, document analysis, feature spec creation, recording analysis, and Flux 2 image generation.

## Features

### 1. PowerPoint Generation

Generate professional PowerPoint presentations from various content sources including text files, documents, images, and more.

**Command:**
```bash
clippy-swe generate-ppt <sources...> --title "Title" --output presentation.pptx
```

**Features:**
- Multi-source content aggregation (text files, PDFs, Word docs, images)
- AI-powered slide outline generation
- Automatic image generation using Flux 2
- Professional layouts and formatting
- Support for content, two-column, and image slides

**Examples:**
```bash
# Generate from text files
clippy-swe generate-ppt content1.txt content2.md --title "Quarterly Report"

# Generate with custom images using Flux 2
clippy-swe generate-ppt report.pdf --generate-images --flux-key YOUR_API_KEY

# Generate without images
clippy-swe generate-ppt data.txt --no-images --title "Data Analysis"
```

### 2. Document Analysis

Analyze documents (PDF, Word, Excel, PowerPoint) and extract key information, summaries, and insights.

**Command:**
```bash
clippy-swe analyze-doc <file> --output analysis.txt
```

**Supported Formats:**
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)
- PowerPoint (.pptx, .ppt)
- Text files (.txt, .md, .py, .js, etc.)

**Features:**
- Content extraction
- AI-powered summary generation
- Key points identification
- Metadata analysis
- Multi-format support

**Examples:**
```bash
# Analyze PDF document
clippy-swe analyze-doc report.pdf

# Analyze and save results
clippy-swe analyze-doc document.docx --output analysis.txt

# Analyze Excel spreadsheet
clippy-swe analyze-doc data.xlsx --verbose
```

### 3. Feature Specification Creation

Create comprehensive feature specification documents with architecture diagrams, requirements, user stories, and more.

**Command:**
```bash
clippy-swe create-spec "Feature description" --output spec.md
```

**Includes:**
- Executive Summary
- Feature Overview
- User Stories
- Technical Requirements
- Architecture Overview
- API Specifications
- Database Schema
- UI/UX Requirements
- Testing Strategy
- Deployment Plan
- Success Metrics
- Timeline and Milestones

**Features:**
- AI-generated comprehensive specifications
- Architecture diagrams using Flux 2
- User flow diagrams
- Database schema visualizations
- Markdown formatting

**Examples:**
```bash
# Create feature spec
clippy-swe create-spec "User authentication system" --output auth_spec.md

# Create with diagrams
clippy-swe create-spec "Real-time chat feature" --diagrams --flux-key YOUR_KEY

# Create without diagrams
clippy-swe create-spec "Payment integration" --no-diagrams
```

### 4. Recording Analysis

Analyze audio and video recordings to generate transcripts, summaries, action items, and insights.

**Command:**
```bash
clippy-swe analyze-recording <file> --output analysis.txt
```

**Features:**
- Automatic transcription (with speech-to-text API)
- AI-powered analysis
- Action items extraction
- Key topics identification
- Speaker insights
- Timeline generation

**Output Includes:**
- Executive Summary
- Key Topics Discussed
- Action Items
- Decisions Made
- Follow-up Questions
- Speaker Insights
- Timeline of Discussion

**Examples:**
```bash
# Analyze meeting recording
clippy-swe analyze-recording meeting.mp4

# Analyze with existing transcript
clippy-swe analyze-recording call.mp3 --transcript transcript.txt

# Analyze and save
clippy-swe analyze-recording webinar.mp4 --output analysis.md
```

### 5. Flux 2 Image Generation

Generate high-quality images using the latest Flux 2 models from text prompts.

**Command:**
```bash
clippy-swe generate-image "prompt" --output image.png
```

**Features:**
- State-of-the-art Flux 2 model
- Customizable dimensions
- High-quality output
- Fast generation
- Professional results

**Examples:**
```bash
# Generate image
clippy-swe generate-image "A futuristic city skyline" --flux-key YOUR_KEY

# Custom dimensions
clippy-swe generate-image "Software architecture diagram" --width 1920 --height 1080

# Generate diagram for documentation
clippy-swe generate-image "Database schema for e-commerce system" --output schema.png
```

## CLI Commands Summary

| Command | Description | Example |
|---------|-------------|---------|
| `generate-ppt` | Generate PowerPoint from content | `clippy-swe generate-ppt file.txt --title "Report"` |
| `analyze-doc` | Analyze documents | `clippy-swe analyze-doc report.pdf` |
| `create-spec` | Create feature specifications | `clippy-swe create-spec "Feature name"` |
| `analyze-recording` | Analyze audio/video | `clippy-swe analyze-recording meeting.mp4` |
| `generate-image` | Generate images with Flux 2 | `clippy-swe generate-image "prompt"` |

## Configuration

### Flux 2 API Key

To use image generation features, you need a Flux 2 API key from [Black Forest Labs](https://bfl.ml/).

Set it via command line:
```bash
--flux-key YOUR_API_KEY
```

Or set as environment variable:
```bash
export FLUX_API_KEY=your_key_here
```

### Dependencies

Install additional dependencies for document processing:
```bash
pip install python-pptx python-docx PyPDF2 pandas openpyxl pillow requests
```

## Use Cases

### 1. Generate Client Presentation
```bash
# Collect content
clippy-swe analyze-doc project_brief.pdf --output brief.txt
clippy-swe analyze-doc metrics.xlsx --output metrics.txt

# Generate presentation
clippy-swe generate-ppt brief.txt metrics.txt images/ \
    --title "Q4 Results" \
    --subtitle "Client Presentation" \
    --generate-images \
    --flux-key $FLUX_KEY
```

### 2. Document Meeting
```bash
# Analyze recording
clippy-swe analyze-recording team_meeting.mp4 --output meeting_notes.md

# Extract action items
# (automatically included in analysis)
```

### 3. Create Feature Specification
```bash
# Generate comprehensive spec
clippy-swe create-spec "Multi-tenant SaaS platform" \
    --diagrams \
    --flux-key $FLUX_KEY \
    --output platform_spec.md
```

### 4. Analyze Multiple Documents
```bash
# Batch analysis
for file in documents/*.pdf; do
    clippy-swe analyze-doc "$file" --output "analysis_$(basename $file .pdf).txt"
done
```

### 5. Generate Visual Assets
```bash
# Generate architecture diagrams
clippy-swe generate-image "Microservices architecture diagram" --output arch.png

# Generate UI mockups
clippy-swe generate-image "Modern dashboard UI design" --output ui.png

# Generate icons
clippy-swe generate-image "Minimalist app icon" --width 512 --height 512 --output icon.png
```

## Python API

You can also use these features programmatically:

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig
from autogen.cli.document_processor import DocumentProcessor, PowerPointSpec
from pathlib import Path

# Initialize
config = ClippySWEConfig()
agent = ClippySWEAgent(config=config)
processor = DocumentProcessor(agent, flux_api_key="YOUR_KEY")

# Generate PowerPoint
spec = PowerPointSpec(title="My Presentation", subtitle="Powered by Clippy")
result = processor.generate_powerpoint(
    content_sources=[Path("content.txt"), "Additional text"],
    output_path=Path("presentation.pptx"),
    spec=spec,
    generate_images=True
)

# Analyze document
analysis = processor.analyze_document(Path("report.pdf"))
print(f"Summary: {analysis.summary}")
print(f"Key points: {analysis.key_points}")

# Create feature spec
spec_result = processor.create_feature_spec(
    "User authentication system",
    output_path=Path("spec.md"),
    include_diagrams=True
)

# Analyze recording
recording_result = processor.analyze_recording(
    recording_path=Path("meeting.mp4"),
    transcript_path=Path("transcript.txt")  # Optional
)

# Generate image
image_result = processor.generate_image_flux2(
    prompt="Futuristic interface design",
    output_path=Path("design.png"),
    width=1920,
    height=1080
)
```

## Integration with Existing Features

These new capabilities integrate seamlessly with existing Clippy SWE features:

- Use in **interactive mode** for conversational document processing
- Combine with **task execution** for complex workflows
- Integrate with **GitHub issue resolution** for complete solutions
- Leverage **multi-agent collaboration** for better results
- Use with **Windows automation** for end-to-end workflows

## Troubleshooting

### Flux 2 API Errors

If you get API errors:
1. Verify your API key is correct
2. Check your API quota/limits
3. Ensure stable internet connection
4. Try again with shorter prompts

### Document Processing Errors

If document analysis fails:
1. Ensure file format is supported
2. Check file is not corrupted
3. Install required dependencies
4. Try with a different file

### PowerPoint Generation Issues

If PowerPoint generation fails:
1. Verify content sources are accessible
2. Check output directory is writable
3. Ensure python-pptx is installed
4. Try with simpler content first

## Future Enhancements

Planned features:
- Video generation using Flux Video
- Audio generation and voice synthesis
- Advanced template library
- Batch processing capabilities
- Export to multiple formats
- Cloud storage integration
- Collaborative editing features

## Support

For issues or questions:
- GitHub Issues: https://github.com/dayour/Clippy-Kernel/issues
- Documentation: See main README and guides
- Examples: Check `examples/` directory
