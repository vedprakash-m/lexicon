# Product Requirements Document (PRD)

## Lexicon: Universal RAG Dataset Factory

**Version:** 1.0  
**Date:** June 25, 2025  
**Status:** Initial Design  
**Product Owner:** Lexicon Development Team  

---

## 🎯 Executive Summary

### Vision Statement
**Lexicon** is a personal data ingestion and preparation tool that transforms books and documents from various formats into high-quality, structured datasets for personal RAG (Retrieval-Augmented Generation) projects, with a focus on spiritual texts, philosophy, and AI/ML resources.

### Mission
Streamline personal content curation by automating the extraction, processing, and chunking of books and documents into consistent, RAG-ready datasets that serve as knowledge bases for personal AI agent projects.

### Product Name: Lexicon
**"Lexicon"** represents a personal knowledge vocabulary builder - transforming your content collection into intelligent, searchable datasets that empower your AI agents with curated domain expertise.

### Success Criteria
- **Personal Scale**: Process 100-500 books efficiently for personal use
- **Quality**: Achieve 95%+ content extraction accuracy with consistent chunking
- **Performance**: Process average book (300 pages) in under 30 minutes on personal hardware
- **Formats**: Support key personal sources (PDFs, EPUBs, web scraping)
- **Efficiency**: Reduce manual dataset creation time by 90% for personal projects

### Future Vision: Personal Knowledge Infrastructure
**Lexicon Phase 4: Agent-Ready Integration** - Beyond dataset creation, Lexicon will serve as the foundation for personal AI agents by providing:
- **Agent Studio**: Lightweight integration layer for LangChain, LlamaIndex, and custom agents
- **Knowledge Graph Creation**: Relationship mapping between processed content for enhanced retrieval
- **Personal GPT Foundation**: Self-curated knowledge base that truly understands your domain expertise
- **Cross-Text Analysis**: Comparative analysis across multiple translations and commentaries

---

## 🌍 Personal Use Context & Problem Statement

### Personal Challenges with RAG Dataset Creation
1. **Manual Processing Overhead**: Creating quality datasets for personal RAG projects requires significant manual effort
2. **Format Inconsistency**: Personal content collection spans PDFs, EPUBs, web sources requiring different extraction approaches
3. **Quality Variability**: Manual chunking leads to inconsistent quality across different documents
4. **Time Investment**: Each new RAG project requires weeks of data preparation
5. **Domain-Specific Needs**: Spiritual texts, philosophy, and technical books need specialized processing approaches
6. **Repetitive Workflows**: Similar processing steps repeated for each new book or project

### Primary Use Cases
- **Personal RAG Projects**: Building knowledge bases for spiritual guidance, philosophy exploration, and AI/ML learning
- **Content Curation**: Processing personal library of spiritual texts (Bhagavad Gita, Srimad Bhagavatam, Isopanisad)
- **Research Organization**: Structuring academic and technical content for easy retrieval
- **AI Agent Training**: Creating domain-specific datasets for personal AI assistants
- **Knowledge Management**: Maintaining personal digital library in RAG-ready formats

### Current Personal Workflow Limitations
- **Existing Scripture Scrapers**: Manual, one-off solutions for specific sources (BG, SB, ISO scrapers)
- **Generic Tools**: LangChain/LlamaIndex document loaders lack domain awareness for spiritual texts
- **Manual Chunking**: Time-intensive process with inconsistent results
- **Storage Complexity**: No unified approach for organizing processed content

**Lexicon's Personal Value**: Unified personal tool for transforming any content into consistent, high-quality RAG datasets with domain-aware processing.

---

## 🏗️ Product Architecture

### Core Value Proposition
**"Lexicon: Personal RAG dataset preparation tool for transforming your content collection into AI-ready knowledge bases"**

### Lexicon 3-Stage Pipeline Architecture

```
📚 STAGE 1: PERSONAL REGISTRY (Mac Native Frontend)
├── Personal content catalog management
├── Simple progress tracking and status monitoring
├── Basic quality validation and manual review
└── Personal metadata and categorization

⬇️

🔄 STAGE 2: LOCAL INGESTION (Processing Engine)
├── Multi-format content extraction (PDF, EPUB, Web)
├── Domain-aware structure recognition (spiritual texts focus)
├── Quality validation and text cleanup
└── Personal cloud storage integration

⬇️

📊 STAGE 3: RULE-BASED CHUNKING (Export System)
├── Standard size-based chunking with smart boundaries
├── Domain-aware chunking (verses, chapters, sections)
├── Simple quality scoring without AI dependencies
└── Multi-format export (JSON, JSONL, CSV, Parquet)
```

---

## 📋 Functional Requirements

### Stage 1: Personal Registry & Management (Mac Native App)

#### FR1: Personal Content Catalog
- **FR1.1**: Add books/documents via drag-and-drop with basic metadata
- **FR1.2**: Support personal categories (spiritual texts, philosophy, AI/ML, personal development)
- **FR1.3**: Track processing status (todo → processing → completed)
- **FR1.4**: Simple versioning and reprocessing capabilities
- **FR1.5**: Import existing book collections from CSV/JSON
- **FR1.6**: Local file and URL validation

#### FR2: Personal Progress Dashboard
- **FR2.1**: Native Mac interface with real-time status updates
- **FR2.2**: Simple quality metrics (extraction success, chunk counts)
- **FR2.3**: Processing time and resource usage monitoring
- **FR2.4**: Manual priority management with drag-and-drop
- **FR2.5**: Basic search and filtering across personal catalog
- **FR2.6**: Export processing reports and statistics

#### FR3: Personal Quality Control
- **FR3.1**: Simple validation with configurable thresholds
- **FR3.2**: Rule-based quality scoring (no AI dependencies)
- **FR3.3**: Manual review interface for personal quality control
- **FR3.4**: Basic error reporting and retry capabilities
- **FR3.5**: Simple rollback for failed processing
- **FR3.6**: A/B comparison between different chunking approaches

### Stage 2: Local Ingestion System

#### FR4: Personal Content Extraction
- **FR4.1**: Web scraping for key personal sources (Vedabase, Archive.org, Gutenberg)
- **FR4.2**: PDF processing with multiple extraction engines and basic OCR
- **FR4.3**: EPUB/MOBI extraction with metadata preservation
- **FR4.4**: Integration with existing personal scrapers (BG, SB, ISO)
- **FR4.5**: Manual file upload with drag-and-drop validation
- **FR4.6**: Sequential processing with progress tracking
- **FR4.7**: Personal cloud storage backup integration

#### FR5: Content Structure Recognition
- **FR5.1**: Rule-based chapter/section detection with domain-specific patterns
- **FR5.2**: Table of contents extraction and validation
- **FR5.3**: Footnote and citation preservation
- **FR5.4**: Basic image handling (OCR for text content)
- **FR5.5**: Multi-language content support for personal collection
- **FR5.6**: Spiritual text structure recognition (verses, mantras, chapters)
- **FR5.7**: Basic metadata extraction and personal tagging
- **FR5.8**: Sanskrit transliteration support (IAST, Devanagari standards)
- **FR5.9**: Cross-translation verse alignment for comparative analysis
- **FR5.10**: Unique document identification with stable UUIDs for reprocessing

#### FR6: Quality Validation & Enhancement
- **FR6.1**: Content completeness verification (missing pages, encoding issues)
- **FR6.2**: Character encoding detection and cleanup
- **FR6.3**: Simple duplicate detection and removal
- **FR6.4**: Rule-based metadata enrichment (categorization, keyword extraction)
- **FR6.5**: Basic error reporting with manual correction options
- **FR6.6**: Content preview interface for personal review and editing

##### FR6.7: Text Normalization and Standardization
- **FR6.7.1**: Whitespace cleanup (remove excessive spaces, normalize line breaks)
- **FR6.7.2**: Character standardization (convert curly quotes, em-dashes, special Unicode characters)
- **FR6.7.3**: Punctuation normalization (standardize punctuation marks and spacing)
- **FR6.7.4**: Case normalization (optional case standardization for specific content types)

##### FR6.8: Content Structure Cleaning
- **FR6.8.1**: Header/footer removal (page numbers, copyright notices, running headers)
- **FR6.8.2**: Navigation cleanup (remove table of contents, index sections, page references)
- **FR6.8.3**: Format artifact removal (clean PDF conversion artifacts, OCR errors, formatting remnants)
- **FR6.8.4**: Noise filtering (remove advertisements, unrelated sidebars, formatting-only content)

##### FR6.9: Domain-Specific Cleaning
- **FR6.9.1**: Spiritual text cleaning (preserve verse numbers, remove repetitive headers/footers)
- **FR6.9.2**: Academic paper cleaning (handle citations, footnotes, bibliography sections appropriately)
- **FR6.9.3**: Technical book cleaning (preserve code blocks, diagrams references, technical formatting)
- **FR6.9.4**: Web content cleaning (remove navigation, ads, comments, social media widgets)

##### FR6.10: Quality Assurance Cleaning
- **FR6.10.1**: Content density analysis (identify and flag low-content sections)
- **FR6.10.2**: Readability assessment (basic readability scoring for content quality)
- **FR6.10.3**: Structure validation (ensure content follows expected patterns for document type)
- **FR6.10.4**: Completeness verification (check for missing sections, truncated content, corruption)

#### FR6.11: Book Enrichment & Metadata Enhancement
- **FR6.11.1**: Web-based metadata enrichment using Google Books, OpenLibrary APIs
- **FR6.11.2**: ISBN/title-based book identification and cross-referencing
- **FR6.11.3**: Author information enrichment (biography, related works, cross-references)
- **FR6.11.4**: Subject classification and genre tagging from authoritative sources
- **FR6.11.5**: Publication details enhancement (publisher, edition, publication date)
- **FR6.11.6**: Visual asset management (cover images, author photos, publisher logos)
- **FR6.11.7**: Book relationship mapping (translations, editions, related works)
- **FR6.11.8**: Enhanced catalog interface with rich visual and metadata display
- **FR6.11.9**: Cross-text analysis support for comparative studies (especially Vedic translations)
- **FR6.11.10**: Recommendation system for related content discovery

### Stage 3: Rule-Based Chunking System

#### FR7: Multi-Strategy Chunking (No AI Dependencies)
- **FR7.1**: Standard chunking (configurable size-based splitting with smart overlap)
- **FR7.2**: Boundary-aware chunking (sentence, paragraph, section boundaries)
- **FR7.3**: Domain-aware chunking with practical examples:
  - *Spiritual texts*: Preserve verse boundaries (BG 2.47), maintain complete mantras, keep chapter introductions intact
  - *Philosophy*: Preserve complete arguments and logical sequences, maintain dialogue structures
  - *Technical content*: Keep code examples together, preserve step-by-step procedures, maintain diagram references
- **FR7.4**: Structure-based chunking (chapters, verses, sections as natural boundaries)
- **FR7.5**: Quality-focused chunking (rule-based optimization for coherence)
- **FR7.6**: Custom chunking profiles for different content types
- **FR7.7**: Hybrid approaches combining multiple rule-based strategies

#### FR8: Basic Chunk Enhancement (No AI Dependencies)
- **FR8.1**: Rule-based summary generation (first/last sentences, key phrases)
- **FR8.2**: Keyword extraction using frequency analysis and domain dictionaries
- **FR8.3**: Basic metadata tagging (content type, source location, length)
- **FR8.4**: Simple relationship mapping (sequential order, hierarchical structure)
- **FR8.5**: Context preservation with configurable overlap strategies
- **FR8.6**: Rule-based quality scoring (length, completeness, structure)
- **FR8.7**: Source citation and reference tracking

#### FR9: Personal Export System
- **FR9.1**: Standard formats (JSON, JSONL, CSV, Parquet)
- **FR9.2**: RAG framework formats (LangChain, LlamaIndex compatible)
- **FR9.3**: Custom export templates for personal projects
- **FR9.4**: Batch export with compression and integrity verification
- **FR9.5**: Personal cloud storage integration (iCloud, Dropbox, Google Drive)
- **FR9.6**: Local file system organization with configurable directory structures
- **FR9.7**: Markdown export for Obsidian, Notion, and note-taking systems
- **FR9.8**: Portable processing profiles for sharing configurations
- **FR9.9**: Complete archive export for future-proofing and migration
- **FR9.10**: Agent-ready export formats for future AI agent integration

---

## 🛠️ Technical Requirements

### Performance Requirements (Personal Use Scale)
- **TR1**: Process 300-page book in under 30 minutes on personal Mac (8GB RAM, 4 cores - MacBook Air M1 baseline)
- **TR2**: Support sequential processing with intelligent resource management
- **TR3**: Handle books up to 5,000 pages without memory issues
- **TR4**: Reliable processing pipeline with basic error recovery
- **TR5**: Responsive UI with real-time progress updates

### Scalability Requirements (Personal Scale)
- **TR6**: Scale to 1,000+ books in personal catalog with efficient local storage
- **TR7**: Support personal cloud storage integration for backup and sync
- **TR8**: Handle large documents without performance degradation
- **TR9**: Native Mac app with local processing capabilities
- **TR10**: Personal cloud storage ready (iCloud, Dropbox, Google Drive)

### Quality Requirements (Personal Focus)
- **TR11**: 95%+ content extraction accuracy for personal content formats
- **TR12**: Consistent chunk quality across personal processing sessions
- **TR13**: Reliable local processing with minimal failures
- **TR14**: Comprehensive backup and sync with personal cloud storage
- **TR15**: Basic logging and error tracking for personal troubleshooting
- **TR16**: Data cleaning accuracy of 98%+ for noise removal and text normalization
- **TR17**: Format-specific cleaning success rate of 95%+ (PDF artifacts, HTML tags, OCR errors)
- **TR18**: Content structure preservation rate of 99%+ for important elements (verses, chapters, citations)

### Privacy & Personal Data
- **TR19**: Fully local processing with no external dependencies for core functionality
- **TR20**: Personal data encryption for cloud storage integration
- **TR21**: Local data management with personal access control
- **TR22**: Processing history and audit logs for personal reference
- **TR23**: Personal content privacy with no external data sharing

---

## 🎨 User Experience Requirements

### Native Mac Interface
- **UX1**: Intuitive drag-and-drop content management using Tauri's native file system integration
- **UX2**: Real-time progress visualization with React components and native Mac progress indicators
- **UX3**: One-click processing with intelligent status updates
- **UX4**: Native search and filtering with Spotlight-style interface using Tauri APIs
- **UX5**: Interactive quality metrics with modern web-based visualizations

### Personal Workflow Integration
- **UX6**: Mac Shortcuts integration for automated workflows via Tauri shell commands
- **UX7**: Notification Center integration for processing updates using Tauri notification APIs
- **UX8**: Native file system integration with organized output folders via Tauri filesystem APIs
- **UX9**: Personal cloud storage sync with status indicators
- **UX10**: Simple configuration management with React-based preferences interface

### Configuration Management (Personal Focus)
- **UX11**: Simple configuration with sensible defaults
- **UX12**: Processing profiles for personal content types (spiritual texts, philosophy, technical)
- **UX13**: Personal customization options without complex plugin systems
- **UX14**: Single-user configuration management
- **UX15**: Configuration backup and restore for personal settings
- **UX16**: Extensible architecture for future plugin support (post-processing, summarization)
- **UX17**: Profile sharing capability for specialized content types (Vedanta texts, academic papers)

---

## 🔄 Integration Requirements

### Personal System Integration
- **INT1**: Migration from existing scripture scrapers (BG, SB, ISO) with data preservation
- **INT2**: Compatibility with existing personal data formats and structures
- **INT3**: Import tools for existing personal content collections
- **INT4**: Integration with current personal RAG project workflows

### Personal Storage Integration
- **INT5**: iCloud Drive integration for seamless Mac ecosystem sync
- **INT6**: Dropbox and Google Drive integration for cross-platform access
- **INT7**: Local storage organization with configurable directory structures
- **INT8**: Personal backup and versioning system
- **INT9**: Mac filesystem integration with Spotlight search support

### Personal Workflow Integration
- **INT10**: Mac Shortcuts integration for automation
- **INT11**: Finder integration for easy file management
- **INT12**: Native Mac notifications and progress reporting
- **INT13**: Personal productivity tool integration (notes, reminders)
- **INT14**: Simple export to personal RAG frameworks (LangChain, LlamaIndex)

---

## 📊 Personal Success Metrics

### Personal Productivity Metrics
- **M1**: Number of books successfully processed per month (target: 20-50 books)
- **M2**: Average processing time per book (target: <30 minutes for 300 pages)
- **M3**: Content extraction accuracy rate (target: >95% for personal content)
- **M4**: Personal satisfaction with chunk quality (target: meets personal RAG project needs)
- **M5**: Time saved vs. manual processing (target: 90% reduction)

### Personal System Metrics
- **M6**: Processing reliability (target: >95% success rate)
- **M7**: Personal cloud storage sync reliability (target: >99% uptime)
- **M8**: Mac system integration effectiveness (target: seamless workflow)
- **M9**: Personal workflow efficiency improvement (target: 5x faster dataset creation)
- **M10**: Personal content organization quality (target: easily searchable and accessible)

### Personal Technical Metrics
- **M11**: Local processing performance (target: efficient resource usage)
- **M12**: Error rate for personal content types (target: <2%)
- **M13**: Personal data backup reliability (target: 100% data preservation)
- **M14**: Native Mac app responsiveness (target: smooth, responsive interface)
- **M15**: Personal storage efficiency (target: organized, non-redundant storage)

---

## 🗓️ Personal Development Roadmap

### Phase 1: Core Personal Tool (Weeks 1-3)
**Milestone: Functional Mac App for Personal Use**

#### Week 1: Mac Native Registry
- Implement native Mac app with Tauri + React frontend
- Create simple book catalog with drag-and-drop support using React components
- Build personal progress tracking with modern web UI
- Add support for personal content categories

#### Week 2: Local Processing Engine
- Implement PDF and EPUB extraction engines
- Integrate existing scripture scrapers (BG, SB, ISO)
- Add basic quality validation and error handling
- Create local file management system

#### Week 3: Basic Chunking & Export
- Implement rule-based chunking strategies
- Add simple quality scoring without AI dependencies
- Create export system for JSON, JSONL, CSV formats
- Build personal cloud storage integration

### Phase 2: Enhanced Personal Features (Weeks 4-6)
**Milestone: Feature-Complete Personal Tool**

#### Week 4: Advanced Processing
- Add OCR support for scanned PDFs
- Implement domain-aware chunking for spiritual texts
- Enhance web scraping capabilities
- Add batch processing support

#### Week 5: Personal Workflow Integration & Book Enrichment
- Implement Mac Shortcuts integration
- Add Notification Center support
- Create Finder integration for easy file access
- Build metadata enrichment system (Google Books, OpenLibrary APIs)
- Implement visual asset management (cover images, author photos)
- Add book relationship detection and analysis

#### Week 6: Quality & Polish
- Add comprehensive error handling and recovery
- Implement personal backup and versioning
- Create enhanced catalog interface with enriched metadata
- Create user documentation and tutorials
- Optimize performance for personal Mac hardware

### Phase 3: Personal Optimization & Advanced Features (Weeks 7-9)
**Milestone: Production-Ready Personal Tool with Full Enrichment**

#### Week 7: Performance & Reliability
- Optimize processing performance for personal use scale
- Complete book enrichment integration
- Add relationship mapping for spiritual text collections
- Implement visual browsing modes

#### Week 8: Advanced Enrichment Features
- Add translation detection and cross-reference mapping
- Implement recommendation system for related content
- Create comparative analysis tools for multiple editions
- Add advanced filtering and search with enriched metadata

#### Week 9: Final Polish & Documentation
- Add comprehensive logging and debugging tools
- Implement personal data migration from existing scrapers
- Create automated testing for personal content types
- Create comprehensive personal user guide
- Add advanced configuration options
- Implement personal analytics and usage tracking
- Prepare for long-term personal use and maintenance

---

## 🎯 Personal Success Criteria & Validation

### Personal Development Success (3 Months)
- [ ] Process 50+ personal books across key formats (PDF, EPUB, web sources)
- [ ] Achieve 95%+ content extraction accuracy for personal content types
- [ ] Create consistent, high-quality chunks suitable for personal RAG projects
- [ ] Successful migration from existing scripture scrapers with data preservation
- [ ] Seamless integration with personal Mac workflow
- [ ] **Book enrichment success**: 90%+ of books have enhanced metadata and cover images
- [ ] **Relationship mapping**: Accurate detection of related books, translations, and editions
- [ ] **Visual catalog**: Intuitive browsing with cover images and rich metadata display

### Personal Productivity Success (6 Months)
- [ ] 200+ books processed efficiently for personal RAG projects
- [ ] 90%+ time savings compared to manual dataset creation
- [ ] Reliable personal cloud storage integration with backup/sync
- [ ] Personal satisfaction with tool meeting all RAG project needs
- [ ] **Enhanced discovery**: 80%+ of related books discovered through enrichment
- [ ] **Visual organization**: Efficient book management through enhanced catalog interface
- [ ] Stable, reliable operation with minimal maintenance required

### Long-term Personal Value (1 Year)
- [ ] 500+ books processed creating comprehensive personal knowledge base
- [ ] Essential tool for all personal RAI/AI agent projects
- [ ] Consistent, high-quality personal datasets enabling advanced RAG applications
- [ ] Efficient personal workflow with minimal time investment in data preparation
- [ ] Comprehensive personal digital library optimized for AI applications

### Personal Tool Retirement Conditions
- [ ] Personal needs change significantly (no longer building RAG applications)
- [ ] Superior commercial alternatives become available that meet personal requirements
- [ ] Technical maintenance becomes too time-intensive for personal use
- [ ] Personal content processing needs evolve beyond tool capabilities

### Future-Proofing and Migration
- [ ] Complete archive export capability ensures no vendor lock-in
- [ ] Portable data formats enable migration to future platforms
- [ ] Open processing standards maintain long-term accessibility
- [ ] Agent-ready integration layer provides evolution path to AI agents

---

## 🔒 Personal Project Risk Assessment

### Technical Risks
- **PDF Parsing Complexity**: Diverse layouts and scanning quality may challenge extraction accuracy
  - *Mitigation*: Multiple extraction engines (PyMuPDF, pdfplumber, OCR fallback)
- **Performance Bottlenecks**: Large books (5,000+ pages) may strain personal Mac hardware
  - *Mitigation*: Streaming processing, memory management, progress checkpoints
- **OCR Integration**: Accuracy and speed challenges with scanned documents
  - *Mitigation*: Basic Tesseract integration, quality thresholds, manual review options

### Development Risks
- **Timeline Optimism**: 8-week estimate may be ambitious for comprehensive feature set
  - *Mitigation*: MoSCoW prioritization, MVP-first approach, iterative releases
- **Scope Creep**: Feature additions during development may delay core functionality
  - *Mitigation*: Strict adherence to Phase 1 requirements, future feature parking lot

### Data Quality Risks
- **Inconsistent Content**: Some books may consistently produce poor quality chunks despite rule-based efforts
  - *Mitigation*: Quality scoring thresholds, manual review interface, iterative improvement
- **Domain Variations**: Spiritual texts from different traditions may require unique handling
  - *Mitigation*: Configurable profiles, manual override options, incremental learning

### Personal Use Risks
- **Maintenance Burden**: Complex system may require ongoing time investment
  - *Mitigation*: Simple architecture, comprehensive documentation, automated testing
- **Technology Evolution**: Dependencies may become outdated or unsupported
  - *Mitigation*: Standard formats, portable exports, minimal external dependencies

---

## 📝 Appendices

### Appendix A: Lexicon Technical Architecture
[Detailed system architecture diagrams, data flow charts, and component interactions]

### Appendix B: User Journey Maps
[Comprehensive user experience flows for different personas and use cases]

### Appendix C: Competitive Analysis
[In-depth analysis of existing solutions and Lexicon's competitive positioning]

### Appendix D: Market Research
[User interviews, surveys, market size analysis, and adoption projections]

### Appendix E: Implementation Specifications
[Detailed technical specifications, API designs, and integration guidelines]

---

**Lexicon PRD History:**
- v1.0 (June 25, 2025): Initial PRD creation with comprehensive feature set and market analysis

**Review & Approval Process:**
- Technical Architecture Review: [Pending]
- Product Strategy Review: [Pending]  
- Business Model Review: [Pending]
- Final Executive Approval: [Pending]

---

*Lexicon: Personal RAG Dataset Preparation Tool*
