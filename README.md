# Lexicon

> **Professional RAG Dataset Preparation Tool for macOS**

Lexicon is a native macOS application designed for developers, researchers, and data scientists who need high-quality RAG (Retrieval-Augmented Generation) datasets. Built with modern technologies, Lexicon provides a comprehensive solution for web scraping, text processing, metadata enrichment, and dataset export.

## ✨ Key Features

- **🖥️ Native macOS App**: Built with Tauri + React for optimal performance and user experience
- **🐍 Advanced Processing**: Python engine with state-of-the-art text processing libraries
- **🔧 Modular Architecture**: Extensible system supporting multiple content sources and formats
- **🔒 Privacy-First**: All processing happens locally - your data never leaves your machine
- **⚡ High Performance**: Rust backend ensures fast, memory-efficient operations
- **📊 Multiple Export Formats**: Support for JSON, JSONL, Parquet, and Markdown outputs
- **🧠 Intelligent Chunking**: Advanced text segmentation strategies optimized for RAG applications

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

### Core Workflows

1. **Project Management**: Create and manage your dataset projects
2. **Source Configuration**: Set up web scraping sources and rules  
3. **Content Scraping**: Execute scraping jobs with progress monitoring
4. **Batch Processing**: Process large volumes of content efficiently
5. **Advanced Chunking**: Apply sophisticated text segmentation strategies
6. **Export & Deploy**: Export datasets in multiple formats for your RAG applications

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

### For Researchers
- **High-Quality Data**: Advanced text processing ensures clean, accurate datasets
- **Flexible Export**: Multiple formats support various research workflows
- **Reproducible Results**: Deterministic processing ensures consistent outputs
- **Extensible Framework**: Easy to add new content sources and processing rules

### For Data Scientists
- **RAG-Optimized**: Purpose-built for Retrieval-Augmented Generation applications
- **Semantic Chunking**: Intelligent text segmentation preserves meaning and context
- **Quality Metrics**: Built-in analytics for dataset quality assessment
- **Integration Ready**: Compatible with popular ML frameworks and tools

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
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for application and data
- **Network**: Internet connection required for initial setup and content scraping

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

## � License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Acknowledgments
- Built with [Tauri](https://tauri.app/) for native app development
- UI powered by [React](https://reactjs.org/) and [Tailwind CSS](https://tailwindcss.com/)
- Backend processing with [Rust](https://www.rust-lang.org/)
- Text processing with [Python](https://www.python.org/) and advanced NLP libraries

---

**Lexicon** - Professional RAG Dataset Preparation for macOS  
*Building the future of AI-ready datasets*

Please ensure compliance with vedabase.io terms of service and respect copyright laws in your jurisdiction.

---

*Lexicon is developed with reverence for the sacred wisdom of the Vedic tradition and gratitude to all who have preserved and shared this knowledge.*
