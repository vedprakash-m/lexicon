# Lexicon - Project Metadata

## Project Overview

**Lexicon** is a Mac-native universal RAG (Retrieval Augmented Generation) dataset preparation tool built with modern technologies. It provides a comprehensive solution for web scraping, text processing, metadata enrichment, and export of high-quality datasets for AI/ML applications, supporting any text content from technical documentation to literature, business documents to religious texts.

**Current Status**: Production-ready with comprehensive feature set  
**Version**: 1.0.0 (stable release)  
**License**: AGPL-3.0  
**Platform**: macOS native application (Tauri + React)

## Implementation Status

### Current State Assessment (July 2025)
Lexicon has completed its comprehensive development cycle and achieved production readiness with all critical systems fully implemented.

**✅ Production-Ready Systems:**
- React frontend with 65+ UI components
- Python processing engine (28 test files, comprehensive coverage)
- Rust backend with Tauri integration
- Complete project management and onboarding systems
- Advanced chunking and export systems with 9 formats
- Real dashboard integration with live backend data
- Performance metrics with actual system monitoring
- Enhanced error handling with toast notifications
- Complete processing pipeline with Rust-Python integration
- Enterprise-grade security and privacy implementation
- Cloud sync infrastructure with multi-provider support
- Comprehensive deployment and monitoring systems

**✅ Recent Completion - All Major Implementation Gaps Resolved:**
All 14 critical UI implementation gaps identified in July 2025 have been systematically resolved:
- Complete AdvancedChunking component with 4 strategies
- Real file upload integration with global event system
- Settings persistence layer with backend integration
- Scraping controls with pause/resume/cancel functionality
- Export manager pipeline with validation and preview
- Real-time notifications system with backend polling
- Form validation framework with reusable components
- Enhanced help system with functional navigation
- Batch processing job creation with multi-step wizard
- Dynamic sidebar status with real-time data
- Complete keyboard navigation system
- Visual rule editor with comprehensive testing
- Book catalog delete functionality
- Source configuration URL testing

### Production Readiness Achievements

**✅ Phase 6 Production Readiness (COMPLETED: July 2025)**
All critical production requirements successfully implemented:

1. **Real Dashboard Data Integration** ✅ - Live backend statistics, real book counts, processing status
2. **Performance Metrics Implementation** ✅ - Real-time CPU, memory, disk monitoring with sysinfo crate
3. **Enhanced Error Handling** ✅ - Toast notification system replacing all alert() calls
4. **Processing Pipeline Completion** ✅ - Complete Rust-Python integration with async processing
5. **Security & Privacy Implementation** ✅ - AES-256-GCM encryption, RBAC, audit logging
6. **Integration Testing** ✅ - Comprehensive test suite with 14 scenarios covering all workflows
7. **Production Deployment** ✅ - Complete deployment infrastructure with monitoring and health checks
8. **Cloud Sync Implementation** ✅ - Multi-provider cloud sync (iCloud, Google Drive, Dropbox, OneDrive)

**✅ Critical Issues Resolution (July 2025)**
All critical production issues identified during user testing have been resolved:
- Book upload data flow and catalog integration
- Notification persistence across navigation
- Project data persistence and state management
- Performance monitoring with real-time metrics
- Duplicate book detection and management
- Book management operations (delete functionality)
- Sidebar navigation count synchronization
- Backup manager routing configuration

## Technical Architecture

### Core Technology Stack
- **Frontend**: React 18.3.1 + TypeScript + Vite + Tailwind CSS
- **Backend**: Rust + Tauri 2.6.0 (native macOS application)  
- **Processing Engine**: Python 3.9+ with 34 specialized libraries
- **State Management**: Zustand + React Query with localStorage persistence
- **UI Components**: Custom components with Headless UI + Lucide icons
- **Build System**: Vite for frontend, Cargo for Rust, npm for package management
- **Security**: AES-256-GCM encryption, PBKDF2 key derivation, RBAC access control
- **Cloud Sync**: Multi-provider support (iCloud, Google Drive, Dropbox, OneDrive)

### Application Structure
```
lexicon/
├── src/                    # React frontend (TypeScript)
│   ├── components/         # 65+ UI components across 12 categories
│   ├── hooks/             # Custom React hooks for state management
│   ├── store/             # Zustand state management with persistence
│   ├── test/              # Comprehensive test suite (Vitest)
│   └── App.tsx            # Main app with React Router
├── src-tauri/             # Rust backend (Tauri app)
│   ├── src/               # Rust source code with 30+ modules
│   └── Cargo.toml         # Rust dependencies (746 crates)
├── python-engine/         # Python processing engine
│   ├── processors/        # Text processing modules (8 core modules)
│   ├── scrapers/          # Web scraping modules
│   ├── enrichment/        # Metadata enrichment and relationships
│   ├── sync/              # Cloud sync and backup management
│   ├── security/          # Data encryption and privacy
│   └── requirements.txt   # Python dependencies (34 packages)
├── docs/                  # Comprehensive documentation
├── scripts/               # Deployment and utility scripts
└── test_data/             # Sample datasets and test fixtures
```

## Core Features Implemented

### Frontend Application (React + TypeScript)
- **Dashboard**: Real-time overview with live statistics and activity feed
- **Project Management**: Complete lifecycle with localStorage persistence
- **Source Configuration**: Universal content source setup with URL testing
- **Scraping Execution**: Web scraping with progress monitoring and controls (pause/resume/cancel)
- **Batch Processing**: Multi-step wizard with job queue management
- **Advanced Chunking**: 4 sophisticated strategies (fixed-size, semantic, hierarchical, universal)
- **Export Manager**: 9 export formats with validation and preview (JSON, JSONL, Parquet, CSV, etc.)
- **Book Catalog**: Enhanced catalog with search, filtering, and management operations
- **Component Showcase**: 65+ professional UI components with Storybook documentation
- **Onboarding System**: Complete first-time user experience with interactive tours
- **Accessibility**: WCAG 2.1 AA compliant with full keyboard navigation
- **Performance Monitoring**: Real-time metrics dashboard with optimization controls
- **Sync & Backup**: Multi-provider cloud storage with automatic conflict resolution
- **Security Dashboard**: Access control, audit logging, and encryption management

### Python Processing Engine (28 Test Files, 100% Coverage)
- **Universal Text Processing**: Support for all content domains (technical, academic, business, literature, legal, medical, educational, web, religious)
- **Advanced Chunking**: 4 sophisticated strategies with content-aware optimization
- **Web Scraping**: Robust scraping with BeautifulSoup4, requests, aiohttp, and Selenium
- **Text Analysis**: NLTK and spaCy integration for advanced language processing
- **Quality Assessment**: Comprehensive quality metrics with TextStat and langdetect
- **Document Processing**: Multi-format support (PDF, EPUB, DOCX, HTML, Markdown)
- **Export Systems**: 9 export formats with custom templates and compression
- **Metadata Enrichment**: Automatic enhancement with external APIs
- **Batch Processing**: Efficient bulk operations with resource monitoring
- **Security**: Data encryption, audit logging, and privacy protection

### Rust Backend (Tauri Integration)
- **Native Integration**: Tauri 2.6.0 with 746 compiled dependencies
- **Database Layer**: SQLite with comprehensive CRUD operations
- **File System**: Secure file handling with encryption and cleanup
- **Performance Monitoring**: Real-time system metrics collection
- **Security Manager**: AES-256-GCM encryption, RBAC, audit logging
- **Cloud Sync**: Multi-provider synchronization with conflict resolution
- **Background Tasks**: Async processing system with progress tracking
- **Plugin System**: File system, dialog, notification, shell plugins

## Production Deployment

### Deployment Infrastructure
- **Environment Validation**: Automated dependency checking and configuration validation
- **Security Setup**: Automatic encryption key generation and secure configuration
- **Performance Optimization**: Bundle optimization with code splitting and lazy loading
- **Health Monitoring**: Comprehensive system monitoring with alerting
- **Error Reporting**: Structured logging and crash analytics framework
- **Production Packaging**: Native macOS app bundle with DMG installer

### Build Process
- **Frontend Build**: Vite optimization with 9 optimized assets (~736KB total)
- **Rust Compilation**: All 746 dependencies successfully compiled with release optimization
- **Python Integration**: Requirements validation and virtual environment setup
- **Bundle Creation**: Native Lexicon.app and DMG installer generation
- **Quality Assurance**: Automated testing pipeline with 28 Python tests

### Cloud Sync Infrastructure
- **Multi-Provider Support**: iCloud Drive, Google Drive, Dropbox, Microsoft OneDrive
- **Automatic Detection**: Platform-specific cloud service discovery
- **Encryption**: End-to-end encryption with Fernet before cloud storage
- **Conflict Resolution**: Automatic and manual merge strategies
- **Selective Sync**: Pattern-based file filtering and exclusion rules
- **Compression**: Bandwidth and storage optimization

## Development Environment

### Prerequisites
- **macOS 10.15+** (Catalina or later)
- **Node.js 18+** with npm
- **Python 3.9+** with pip
- **Rust 1.77.2+** with Cargo
- **Xcode Command Line Tools**

### Development Workflow
```bash
# Frontend development
npm run dev                # Vite dev server with hot reload
npm run build             # Production build with optimization
npm run storybook         # Component development and documentation

# Tauri development  
npm run tauri dev         # Full app development with hot reload
npm run tauri build       # Production build with native packaging

# Python environment
cd python-engine
pip install -r requirements.txt
python -m pytest          # Run comprehensive test suite (28 files)
```

### Code Quality Standards
- **TypeScript**: Strict mode with comprehensive ESLint configuration
- **React**: Functional components with hooks pattern and proper state management
- **Styling**: Tailwind CSS utility-first with consistent design system
- **Testing**: Vitest for frontend, pytest for Python with 100% backend coverage
- **Documentation**: Storybook for components, comprehensive README files
- **Accessibility**: WCAG 2.1 AA compliance with keyboard navigation
- **Security**: Secure coding practices with encryption and audit logging

## Key Dependencies

### Frontend (React)
- React 18.3.1 with React DOM and Router for SPA architecture
- Zustand for lightweight state management with persistence
- Tanstack Query for server state management and caching
- Tailwind CSS + Headless UI for accessible, responsive styling
- Lucide React for consistent iconography across components
- Class Variance Authority for component variants and theming

### Backend (Rust)
- Tauri 2.6.0 with macOS native API access and plugin system
- SQLite with comprehensive database operations and migrations
- Sysinfo for real-time system performance monitoring
- AES-GCM encryption for data security and privacy
- Multiple Tauri plugins (fs, dialog, notification, shell, clipboard)

### Python Engine (34 Packages)
- **Web Scraping**: requests, beautifulsoup4, lxml, aiohttp, selenium
- **NLP Processing**: nltk, spacy, textstat, langdetect for text analysis
- **Document Processing**: PyMuPDF, pdfplumber, python-docx, ebooklib
- **Data Validation**: pydantic, chardet, ftfy for data integrity
- **Performance**: tqdm, psutil for monitoring and optimization
- **Security**: cryptography for encryption and secure operations

## Architecture Principles

### Design Philosophy
- **Local-First**: All processing happens locally for maximum privacy
- **Privacy-Focused**: No external data transmission without explicit user consent
- **Performance-Optimized**: Native Rust backend with efficient React frontend
- **Universal-Compatible**: Intelligent content recognition for any text domain
- **Extensible**: Modular Python engine for easy feature additions
- **Accessible**: Native macOS experience with full accessibility support
- **Secure**: Enterprise-grade encryption and access control systems

### Quality Assurance
- **Comprehensive Testing**: 28 Python test files with 100% backend coverage
- **Frontend Validation**: Vitest integration tests with Tauri API mocking
- **Code Review**: TypeScript strict mode with ESLint enforcement
- **Performance Monitoring**: Real-time metrics collection and optimization
- **Security Auditing**: Regular security validation and penetration testing
- **Accessibility Validation**: Full WCAG 2.1 AA compliance testing
- **Production Readiness**: Zero placeholder implementations in production build

## Target Users

**Primary Users**: Developers, researchers, data scientists, content creators, analysts, academics, and professionals across all industries requiring high-quality RAG dataset preparation.

**Use Cases**: 
- Technical documentation processing for AI training
- Academic research dataset preparation
- Business content analysis and structuring
- Literature and creative content organization
- Legal document processing and analysis
- Medical content structuring for research
- Educational material preparation
- Web content extraction and processing
- Religious text analysis and organization

**Enterprise Applications**: Large-scale content processing, team collaboration, advanced analytics, compliance reporting, and enterprise integrations.

---

*Last Updated: July 20, 2025*  
*Status: Production-ready with comprehensive feature set*  
*Next Phase: Community engagement and enterprise feature development*
