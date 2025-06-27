#!/usr/bin/env python3
"""
Quality Analysis System Demo

This script demonstrates the capabilities of the quality analysis system
by analyzing various types of documents and generating comprehensive reports.

Author: Lexicon Development Team
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.quality_analyzer import QualityAnalysisEngine
import json

def demo_quality_analysis():
    """Demonstrate the quality analysis system."""
    print("🔍 Quality Analysis System Demo")
    print("=" * 50)
    
    # Create analysis engine
    engine = QualityAnalysisEngine({
        'thresholds': {
            'min_length': 50,
            'min_words': 10,
            'max_noise_ratio': 0.2
        }
    })
    
    # Sample documents for analysis
    documents = [
        {
            'id': 'perfect_doc',
            'text': """
            Complete Document with Excellent Structure
            
            This document demonstrates perfect structure and quality standards.
            It contains well-organized content with clear sections and appropriate
            length. The writing is coherent and follows best practices.
            
            The content provides valuable information in a clear manner,
            with proper formatting and structure that enhances readability.
            Each paragraph flows naturally into the next, creating a
            cohesive narrative that engages the reader.
            
            In conclusion, this document exemplifies the quality standards
            we strive to achieve in our content creation process.
            """,
            'type': 'general',
            'expected_sections': ['Introduction', 'Content', 'Conclusion']
        },
        {
            'id': 'short_doc',
            'text': "Very brief document.",
            'type': 'general'
        },
        {
            'id': 'noisy_doc',
            'text': """
            Document   with    lots     of    noise!!!
            
            
            
            This    document    has    excessive    whitespace    and    
            formatting    issues.    It    contains    many    artifacts
            from    poor    processing    and    needs    cleanup.
            
            The     content     is     also     very     repetitive     and
            repetitive     and     repetitive     with     poor     quality.
            """,
            'type': 'general'
        },
        {
            'id': 'spiritual_verse',
            'text': """
            Bhagavad Gita 2.47
            
            karmaṇy evādhikāras te mā phaleṣu kadācana
            mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi
            
            Translation:
            You have a right to perform your prescribed duty, but do not claim 
            entitlement to the fruits of action. Never consider yourself the cause 
            of the results of your activities, and never be attached to not doing your duty.
            
            Purport:
            This verse establishes one of the fundamental principles of karma-yoga - 
            the yoga of action. The Supreme Lord Krishna instructs Arjuna about the 
            proper attitude one should maintain while performing prescribed duties.
            """,
            'type': 'spiritual'
        },
        {
            'id': 'incomplete_article',
            'text': """
            Incomplete Research Article
            
            This article attempts to discuss an important topic but lacks
            proper structure and completeness. It has a title but is missing
            several key sections that would make it complete.
            
            The methodology section is entirely absent, and there are no
            results or discussion sections present in this document.
            """,
            'type': 'general',
            'expected_sections': ['Introduction', 'Methodology', 'Results', 'Discussion', 'Conclusion']
        }
    ]
    
    print(f"📊 Analyzing {len(documents)} documents...\n")
    
    # Perform batch analysis
    result = engine.analyze_batch(documents)
    
    # Display individual results
    print("📋 Individual Document Analysis Results:")
    print("-" * 50)
    
    for doc_result in result['individual_results']:
        doc_id = doc_result['document_id']
        
        if doc_result.get('analysis_failed'):
            print(f"❌ {doc_id}: Analysis failed - {doc_result.get('error')}")
            continue
            
        quality_score = doc_result['anomaly_report']['overall_score']
        completeness = doc_result['completeness_metrics']['percentage']
        issues = doc_result['anomaly_report']['total_issues']
        
        print(f"📄 Document: {doc_id}")
        print(f"   Quality Score: {quality_score:.2f}")
        print(f"   Completeness: {completeness}%")
        print(f"   Issues Found: {issues}")
        
        if doc_result['recommendations']:
            print("   Recommendations:")
            for rec in doc_result['recommendations'][:3]:  # Show top 3
                print(f"   • {rec}")
        print()
    
    # Display batch report summary
    print("📈 Batch Analysis Summary:")
    print("-" * 50)
    
    summary = result['batch_report']['summary']
    print(f"Total Documents: {summary['total_documents']}")
    print(f"Average Quality Score: {summary['average_quality_score']:.2f}")
    print(f"Quality Grade: {summary['quality_grade']}")
    print(f"Documents with Issues: {summary['documents_with_issues']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Average Completeness: {summary['average_completeness']:.1%}")
    
    # Display top recommendations
    recommendations = result['batch_report']['recommendations']
    if recommendations:
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    # Display anomaly analysis
    anomaly_analysis = result['batch_report']['anomaly_analysis']
    if anomaly_analysis.get('most_common_issues'):
        print(f"\n🚨 Most Common Issues:")
        for issue_type, count in anomaly_analysis['most_common_issues']:
            print(f"   • {issue_type}: {count} occurrences")
    
    # Display completeness analysis
    completeness_analysis = result['batch_report']['completeness_analysis']
    if completeness_analysis.get('most_missing_sections'):
        print(f"\n📋 Most Missing Sections:")
        for section, count in completeness_analysis['most_missing_sections']:
            print(f"   • {section}: missing in {count} documents")
    
    print("\n" + "=" * 50)
    print("✅ Quality Analysis Demo Complete!")
    
    # Optionally save detailed report
    save_report = input("\n💾 Save detailed report to file? (y/n): ").lower().strip() == 'y'
    if save_report:
        output_file = 'quality_analysis_demo_report.json'
        engine.save_report(result['batch_report'], output_file)
        print(f"📁 Detailed report saved to: {output_file}")

if __name__ == "__main__":
    demo_quality_analysis()
