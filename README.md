# Lexicon

> **Universal RAG Dataset Preparation Tool for Any Text Content**

Lexicon is a native macOS application designed for developers, researchers, content creators, analysts, and professionals who need high-quality RAG (Retrieval-Augmented Generation) datasets from any text content. Built with modern technologies, Lexicon provides a comprehensive solution for processing technical documentation, academic papers, business documents, literature, legal texts, medical content, educational materials, web content, religious texts, and any structured text.

> **Note**: Lexicon is currently in active development. Core processing capabilities are implemented and tested, with the user interface and integration features being refined for production release.

## ✨ Key Features

- **🖥️ Native macOS App**: Built with Tauri + React for optimal performance and user experience
- **🌍 Universal Content Support**: Process technical docs, academic papers, business content, literature, legal texts, medical content, educational materials, web content, and religious texts
- **🐍 Advanced Processing**: Python engine with intelligent content recognition and processing capabilities
- **🔧 Modular Architecture**: Extensible system supporting any text content source and format
- **🔒 Privacy-First**: All processing happens locally - your content never leaves your machine
- **⚡ High Performance**: Rust backend ensures fast, memory-efficient operations for large content collections
- **📊 Multiple Export Formats**: Support for JSON, JSONL, Parquet, CSV, and Markdown outputs optimized for any content analysis
- **🧠 Intelligent Chunking**: Advanced text segmentation strategies preserving document structure and content formatting

## 🏗️ Architecture

Lexicon combines the best of three technologies:

- **Frontend**: React 18 + TypeScript + Tailwind CSS for a modern, responsive interface
- **Backend**: Rust + Tauri for native macOS performance and security
- **Processing**: Python engine with advanced NLP libraries for intelligent content processing

## 🚀 Quick Start

### Prerequisites

- macOS 10.15+ (Catalina or later)
- Node.js 18+
- Python 3.9+
- Rust 1.77.2+

### Installation

```bash
# Clone the repository
git clone https://github.com/vedprakash-m/lexicon.git
cd lexicon

# Install frontend dependencies
npm install

# Install Python dependencies
cd python-engine
pip install -r requirements.txt
cd ..

# Run the development version
npm run tauri dev
```

### Building for Production

```bash
# Build the application
npm run tauri build
```

## 🎯 Use Cases

### For Developers
- **API Documentation**: Process technical documentation for code assistant training
- **Code Comments**: Extract and structure inline documentation
- **Technical Specifications**: Convert specs into searchable knowledge bases

### For Researchers
- **Academic Papers**: Structure research papers for literature review automation
- **Citation Analysis**: Extract and organize academic references
- **Research Data**: Process research findings into queryable datasets

### For Content Creators
- **Article Processing**: Convert blog posts and articles into structured data
- **Documentation**: Transform user manuals into interactive knowledge bases
- **Educational Content**: Structure courses and tutorials for learning systems

### For Business Analysts
- **Report Processing**: Extract insights from business reports and presentations
- **Policy Documents**: Structure organizational policies for compliance systems
- **Market Research**: Process market analysis reports into actionable data

## 🔧 Core Capabilities

### Content Processing
- **Multi-format Support**: PDF, EPUB, DOCX, HTML, Markdown, and plain text (via PyMuPDF, pdfplumber, ebooklib, python-docx)
- **Web Scraping**: Intelligent extraction from websites using requests, BeautifulSoup4, and aiohttp
- **Quality Analysis**: Comprehensive quality assessment with 930+ lines of quality analyzer code
- **Language Detection**: Multi-language support with langdetect and character encoding detection

### Chunking Strategies
- **Fixed-size Chunking**: Consistent chunk sizes with smart boundary detection
- **Semantic Chunking**: Content-aware segmentation preserving meaning (requires sentence-transformers)
- **Hierarchical Chunking**: Structure-preserving chunking for complex documents
- **Universal Content Chunking**: Intelligent adaptation to any content type with 1000+ lines of chunking logic

### Export Options
- **JSON/JSONL**: Standard formats for LangChain, LlamaIndex integration
- **Parquet**: Columnar format for data analysis (via PyArrow)
- **CSV/TSV**: Spreadsheet-compatible formats for data manipulation
- **XML/Markdown**: Structured and human-readable formats
- **Custom formats**: Extensible export system with compression support

## 📊 Performance

- **Processing Speed**: Target of 300-page document in under 30 minutes
- **Quality Target**: 95%+ content extraction accuracy goal
- **Scale**: Designed for personal and small team use with 100-500 documents
- **Memory Efficiency**: Optimized for local processing with minimal resource usage

## 🛠️ Development

### Frontend Development
```bash
npm run dev          # Start Vite dev server
npm run build        # Production build
npm run storybook    # Component development
```

### Backend Development
```bash
npm run tauri dev    # Full application development
npm run tauri build  # Production application build
```

### Python Engine
```bash
cd python-engine
python -m pytest    # Run comprehensive test suite
python processors/test_chunking_strategies.py  # Test chunking strategies
```

## 🧪 Testing

Lexicon includes comprehensive testing across all components:

- **Frontend**: Vitest for React component testing (106 TypeScript/React files)
- **Backend**: Rust unit tests for Tauri integration
- **Python**: 28 test files with coverage of processing capabilities
- **Component Development**: Storybook setup for UI component development

```bash
# Run tests
npm run test        # Frontend tests
cd python-engine && python -m pytest  # Python tests
npm run storybook   # Component development environment
```

## 📚 Documentation

- **[Product Requirements](docs/PRD-Lexicon.md)**: Complete product specification
- **[Technical Specification](docs/Tech_Spec_Lexicon.md)**: Detailed technical architecture
- **[User Experience](docs/User_Experience.md)**: User interface and workflow design
- **[Implementation Tasks](docs/lexicon-tasks.md)**: Development roadmap and progress
- **[Project Metadata](docs/metadata.md)**: Current implementation status

## 🤝 Contributing

We welcome contributions to Lexicon! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code of conduct and community standards
- Development setup and workflow
- Pull request process and code review
- Testing requirements and documentation standards

## 📄 License

This project is licensed under the GNU Affero General Public License, version 3 (AGPLv3) - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [https://github.com/vedprakash-m/lexicon](https://github.com/vedprakash-m/lexicon)
- **Issues**: [https://github.com/vedprakash-m/lexicon/issues](https://github.com/vedprakash-m/lexicon/issues)
- **Discussions**: [https://github.com/vedprakash-m/lexicon/discussions](https://github.com/vedprakash-m/lexicon/discussions)

---

**Made with ❤️ for developers, researchers, and content creators who need high-quality RAG datasets.**
