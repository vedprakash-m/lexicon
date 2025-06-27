# Lexicon - Project Metadata

## Project Overview
**Lexicon** is a Mac-native RAG (Retrieval Augmented Generation) dataset preparation tool built with modern technologies. It provides a comprehensive solution for web scraping, text processing, metadata enrichment, and export of high-quality datasets for AI/ML applications.

## Technical Architecture

### Core Technologies
- **Frontend**: React 18.3.1 + TypeScript + Vite + Tailwind CSS
- **Backend**: Rust + Tauri 2.6.0 (native macOS application)  
- **Processing Engine**: Python 3.9+ with advanced text processing libraries
- **State Management**: Zustand + React Query
- **UI Components**: Custom components with Headless UI + Lucide icons
- **Build System**: Vite for frontend, Cargo for Rust, npm for package management

### Application Structure
```
lexicon/
├── src/                    # React frontend (TypeScript)
│   ├── components/         # UI components with routing
│   ├── hooks/             # Custom React hooks  
│   ├── store/             # Zustand state management
│   └── App.tsx            # Main app with React Router
├── src-tauri/             # Rust backend (Tauri app)
│   ├── src/               # Rust source code
│   └── Cargo.toml         # Rust dependencies
├── python-engine/         # Python processing engine
│   ├── processors/        # Text processing modules
│   ├── scrapers/          # Web scraping modules
│   └── requirements.txt   # Python dependencies
└── data/                  # Sample datasets and storage
```

## Core Features Implemented

### Frontend Application
- **Dashboard**: Main overview interface
- **Project Management**: Project creation and management
- **Source Configuration**: Configure scraping sources  
- **Scraping Execution**: Web scraping interface
- **Batch Processing**: Bulk data processing
- **Advanced Chunking**: Text chunking strategies
- **Component Showcase**: UI component library

### Python Processing Engine
- **Web Scraping**: Robust scraping with BeautifulSoup4, requests, aiohttp
- **Text Processing**: NLTK, spaCy for advanced text analysis
- **Quality Analysis**: TextStat, langdetect for content quality assessment
- **Document Processing**: PyMuPDF, pdfplumber for PDF handling
- **Character Encoding**: chardet, ftfy for text normalization
- **Progress Tracking**: tqdm, psutil for monitoring
- **Data Validation**: Pydantic for data models

### Rust Backend  
- **Native Integration**: Tauri for native macOS functionality
- **Plugin System**: File system, dialog, notification, shell plugins
- **HTTP Client**: Built-in HTTP handling
- **Build System**: Comprehensive Cargo configuration

## Development Environment

### Prerequisites
- **macOS 10.15+** (Catalina or later)
- **Node.js 18+** with npm/yarn
- **Python 3.9+** with pip
- **Rust 1.77.2+** with Cargo
- **Xcode Command Line Tools**

### Development Workflow
```bash
# Frontend development
npm run dev                # Vite dev server
npm run build             # Production build
npm run storybook         # Component development

# Tauri development  
npm run tauri dev         # Full app development
npm run tauri build       # Production build

# Python environment
cd python-engine
pip install -r requirements.txt
```

### Code Quality Standards
- **TypeScript**: Strict mode enabled with ESLint
- **React**: Functional components with hooks
- **Styling**: Tailwind CSS utility-first approach
- **Testing**: Vitest for unit testing
- **Documentation**: Storybook for component documentation

## Project Status
- **Version**: 1.0.0
- **License**: MIT
- **Development Phase**: Active development
- **Platform**: macOS native application
- **Target Users**: Developers, researchers, data scientists

## Key Dependencies

### Frontend
- React 18.3.1 with React DOM and Router
- Zustand for state management
- Tanstack Query for server state
- Tailwind CSS + Headless UI for styling
- Lucide React for icons
- Class Variance Authority for component variants

### Backend (Rust)
- Tauri 2.6.0 with macOS private API access
- Multiple Tauri plugins (fs, dialog, notification, shell)
- HTTP and JSON handling capabilities

### Python Engine
- requests, beautifulsoup4, lxml for web scraping
- aiohttp for async HTTP operations
- nltk, spacy for natural language processing
- textstat, langdetect for text analysis
- PyMuPDF, pdfplumber for document processing
- pydantic for data validation

## Development Guidelines
- **Local-First**: All processing happens locally
- **Privacy-Focused**: No data transmission without consent
- **Performance-Optimized**: Native Rust backend with efficient React frontend
- **Extensible**: Modular Python engine for easy feature additions
- **User-Friendly**: Native macOS experience with intuitive workflows

## Git Configuration
- Repository includes .gitignore for Node.js, Rust, Python, and macOS
- Git repository already initialized
- Standard branching and commit conventions

## Contributing Information
The project follows standard open-source contribution practices:
- Issue reporting with templates
- Pull request workflow with feature branches
- Code quality standards for TypeScript, Rust, and Python
- Comprehensive testing requirements
- Documentation updates for changes

---
*Generated: June 26, 2025*  
*Based on: CONTRIBUTING.md, PROJECT_STRUCTURE.md analysis and codebase validation*
