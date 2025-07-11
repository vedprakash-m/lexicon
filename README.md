# Lexicon- **🌍 Universal Content Support**: Process technical docs, academic papers, business content, literature, legal texts, medical content, educational materials, web content, and religious texts
- **🐍 Advanced Processing**: Python engine with intelligent content recognition and processing capabilities
- **🔧 Modular Architecture**: Extensible system supporting any text content source and format
- **🔒 Privacy-First**: All processing happens locally - your content never leaves your machine
- **⚡ High Performance**: Rust backend ensures fast, memory-efficient operations for large content collections
- **📊 Multiple Export Formats**: Support for JSON, JSONL, Parquet, and Markdown outputs optimized for any content analysis
- **🧠 Intelligent Chunking**: Advanced text segmentation strategies preserving document structure and content formattingniversal RAG Dataset Preparation Tool for Any Text Content**

Lexicon is a native macOS application designed for developers, researchers, content creators, analysts, and professionals who need high-quality RAG (Retrieval-Augmented Generation) datasets from any text content. Built with modern technologies, Lexicon provides a comprehensive solution for processing technical documentation, academic papers, business documents, literature, legal texts, medical content, educational materials, web content, religious texts, and any structured text.

## ✨ Key Features

- **🖥️ Native macOS App**: Built with Tauri + React for optimal performance and user experience
- **� Universal Scripture Support**: Process Bible, Quran, Torah, Buddhist texts, Hindu scriptures, and classical philosophy
- **�🐍 Advanced Processing**: Python engine with specialized structured scripture processing capabilities
- **🔧 Modular Architecture**: Extensible system supporting multiple religious and classical text sources
- **🔒 Privacy-First**: All processing happens locally - your sacred texts never leave your machine
- **⚡ High Performance**: Rust backend ensures fast, memory-efficient operations for large religious text collections
- **📊 Multiple Export Formats**: Support for JSON, JSONL, Parquet, and Markdown outputs optimized for religious text analysis
- **🧠 Intelligent Chunking**: Advanced text segmentation strategies preserving verse structure and religious text formatting

## 🏗️ Architecture

Lexicon combines the best of three technologies:

- **Frontend**: React 18 + TypeScript + Tailwind CSS for a modern, responsive UI
- **Backend**: Rust + Tauri for native performance and system integration  
- **Processing Engine**: Python 3.9+ with advanced NLP libraries for text processing

### Technology Stack
- **UI Framework**: React 18.3.1 with React Router
- **State Management**: Zustand + TanStack Query
- **Styling**: Tailwind CSS + Headless UI
- **Backend**: Rust with Tauri 2.6.0
- **Processing**: Python with NLTK, spaCy, BeautifulSoup4
- **Build System**: Vite + Cargo + npm

## � Getting Started

### Prerequisites

- **macOS 10.15+** (Catalina or later)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
- **Python 3.9+** - Available via Homebrew: `brew install python`
- **Rust 1.77+** - Install via [rustup.rs](https://rustup.rs/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/lexicon.git
   cd lexicon
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Set up Python environment**:
   ```bash
   cd python-engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   ```

4. **Install Tauri CLI** (if not already installed):
   ```bash
   cargo install tauri-cli --version ^2.0.0
   ```

### Development

Run the development server:
```bash
npm run tauri dev
```

Build for production:
```bash
npm run tauri build
```

## 📜 License

This project is licensed under the GNU Affero General Public License, version 3 (AGPLv3). See the `LICENSE` file for the full license text.

### Core Workflows

1. **Project Management**: Create and manage your religious or classical text dataset projects
2. **Source Configuration**: Set up web scraping sources and rules for religious websites and archives
3. **Content Scraping**: Execute scraping jobs with progress monitoring for large religious text collections
4. **Batch Processing**: Process large volumes of religious and classical texts efficiently
5. **Advanced Chunking**: Apply sophisticated text segmentation strategies preserving religious text structure
6. **Export & Deploy**: Export datasets in multiple formats optimized for religious text analysis and RAG applications

## 📁 Project Structure

```
lexicon/
├── src/                    # React frontend application
│   ├── components/         # Reusable UI components
│   ├── hooks/             # Custom React hooks
│   └── store/             # State management
├── src-tauri/             # Rust backend (native app)
│   └── src/               # Rust source code
├── python-engine/         # Python processing engine
│   ├── processors/        # Text processing modules
│   ├── scrapers/          # Web scraping modules
│   └── requirements.txt   # Python dependencies
├── docs/                  # Project documentation
└── data/                  # Sample datasets and storage
```
## 🏆 Key Benefits

### For Developers
- **Modern Stack**: Built with latest React, Rust, and Python technologies
- **Type Safety**: Full TypeScript integration with comprehensive type definitions
- **Testing Ready**: Vitest setup for unit testing and quality assurance
- **Documentation**: Storybook integration for component development

### For Religious Scholars & Researchers
- **Universal Text Support**: Process texts from Christianity, Islam, Judaism, Buddhism, Hinduism, and classical philosophy
- **Verse-Aware Processing**: Intelligent handling of religious text structure including verses, chapters, and sections
- **High-Quality Data**: Advanced text processing ensures clean, accurate datasets preserving religious formatting
- **Flexible Export**: Multiple formats support various research workflows and religious studies applications
- **Reproducible Results**: Deterministic processing ensures consistent outputs for academic research
- **Extensible Framework**: Easy to add new religious text sources and processing rules

### For Data Scientists
- **RAG-Optimized**: Purpose-built for Retrieval-Augmented Generation applications with religious and classical texts
- **Semantic Chunking**: Intelligent text segmentation preserves meaning and religious context
- **Quality Metrics**: Built-in analytics for dataset quality assessment
- **Integration Ready**: Compatible with popular ML frameworks and tools for religious text analysis

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices for frontend code
- Use Rust idioms and proper error handling for backend code
- Include tests for new functionality
- Update documentation for user-facing changes
- Maintain code quality with provided linting tools

## � Requirements

### System Requirements
- **Operating System**: macOS 10.15 (Catalina) or later
- **Memory**: 4GB RAM minimum, 8GB recommended for large religious text collections
- **Storage**: 2GB free space for application and religious text data
- **Network**: Internet connection required for initial setup and religious text scraping

### Development Requirements
- **Node.js**: 18.x or later
- **Python**: 3.9 or later
- **Rust**: 1.77 or later
- **Git**: For version control

## � Support

### Documentation
- **Technical Specs**: See `docs/Tech_Spec_Lexicon.md` for detailed technical information
- **Product Requirements**: See `docs/PRD-Lexicon.md` for product specifications
- **User Experience**: See `docs/User_Experience.md` for UI/UX guidelines
- **Task List**: See `docs/lexicon-tasks.md` for development progress

### Getting Help
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas
- **Documentation**: Check the docs folder for comprehensive guides

---

**Lexicon** - Universal RAG Dataset Preparation for Religious and Classical Texts  
*Building the future of AI-ready religious and classical text datasets*

---
