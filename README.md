# Podcast Script Generator

A streamlined web application that transforms any content into engaging podcast scripts using AI (Google Gemini & DeepSeek).

## Features

- **Multi-source Input**: Process text, URLs, or files
- **AI-Powered Analysis**: Extract themes and key concepts automatically
- **Quality Script Generation**: Draft, elaborate, and polish in one pipeline
- **Modern Web UI**: Clean, responsive interface
- **Fast Processing**: Optimized workflow with optional step skipping
- **Export Options**: Copy to clipboard or download as text file

## Architecture

### Streamlined Pipeline

1. **Text Analysis** (Gemini)
   - Extract themes and topics
   - Identify key concepts
   - Chunk content intelligently

2. **Script Generation** (DeepSeek)
   - Generate conversational draft
   - Elaborate with examples
   - Polish for final quality

3. **Web Interface** (Flask)
   - Clean, modern UI
   - Real-time progress updates
   - Easy export options

##  Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key
- DeepSeek API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd podcast-script-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
podcast-script-generator/
├── app/
│   ├── core/
│   │   ├── api_clients.py      # Gemini & DeepSeek clients
│   │   ├── text_analyzer.py    # Content analysis
│   │   ├── script_generator.py # Script creation
│   │   └── pipeline.py          # Main orchestrator
│   ├── static/
│   │   ├── css/style.css        # Modern styling
│   │   └── js/app.js            # Frontend logic
│   └── templates/
│       └── index.html           # Main UI
├── config/
│   └── config.py                # Configuration
├── outputs/                     # Generated files
├── logs/                        # Application logs
├── app.py                       # Flask application
├── requirements.txt             # Dependencies
└── .env                         # Environment variables
```

##  Configuration

Edit `config/config.py` to customize:

- **Pipeline settings**: chunk sizes, max concepts, etc.
- **API configuration**: models, timeouts, retries
- **Podcast metadata**: default names and styles

##  Usage

### Basic Usage

1. Enter or paste your content in the text area
2. Customize podcast name and host name
3. Click "Generate Script"
4. Copy or download your script

### Advanced Options

- **Max Concepts**: Control depth of analysis (8-20)
- **Skip Elaboration**: Faster generation, shorter script
- **Skip Polishing**: Skip final refinement step

### API Endpoints

- `GET /` - Main web interface
- `POST /api/generate` - Generate script
- `GET /api/health` - Health check
- `GET /api/download/<filename>` - Download script

##  Deployment

### Local Development

```bash
python app.py
```

### Production (Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

##  Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `DEEPSEEK_KEY` | DeepSeek API key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `PORT` | Server port (default: 5000) | No |
| `LOG_LEVEL` | Logging level (default: INFO) | No |

## Performance

- **Analysis**: ~30-60 seconds
- **Script Generation**: ~60-120 seconds
- **Total**: ~2-3 minutes for complete script

Performance varies based on content length and selected options.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request


##  Troubleshooting

### API Key Issues
- Verify keys are correctly set in `.env`
- Check API key validity with providers

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Generation Failures
- Check API quotas and limits
- Review logs in `logs/` directory
- Try with smaller content or skip options enabled

##  Customization

### UI Styling
Edit `app/static/css/style.css` to customize colors, fonts, and layout.

### Prompts
Modify prompts in `app/core/text_analyzer.py` and `app/core/script_generator.py`.

### Pipeline
Adjust workflow in `app/core/pipeline.py` to add/remove steps.

##  Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs for error details

---

