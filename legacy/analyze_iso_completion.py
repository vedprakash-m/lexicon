#!/usr/bin/env python3
"""
Comprehensive analysis tool for Śrī Īśopaniṣad scraping completion
Analyzes all scraped data to determine completeness of mantras (verses)
"""

import json
import os
from typing import Dict, List

def analyze_isopanisad_data() -> Dict:
    """Analyze the complete sri_isopanisad_complete.json file"""
    filename = 'data_iso/raw/sri_isopanisad_complete.json'
    
    if not os.path.exists(filename):
        return {
            'exists': False,
            'mantras': 0,
            'status': 'MISSING'
        }
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mantras = data.get('mantras', [])
        mantra_count = len(mantras)
        title = data.get('title', 'Śrī Īśopaniṣad')
        
        # Check content quality
        mantras_with_sanskrit = 0
        mantras_with_translation = 0
        mantras_with_purport = 0
        mantras_with_synonyms = 0
        
        # Track individual mantras covered
        covered_mantras = set()
        mantra_details = []
        has_invocation = False
        
        for mantra in mantras:
            sanskrit = mantra.get('sanskrit_mantra', '').strip()
            translation = mantra.get('translation', '').strip()
            purport = mantra.get('purport', '').strip()
            synonyms = mantra.get('synonyms', '').strip()
            mantra_number = mantra.get('mantra_number', '')
            mantra_numbers = mantra.get('mantra_numbers', [])
            
            if sanskrit:
                mantras_with_sanskrit += 1
            if translation:
                mantras_with_translation += 1
            if purport:
                mantras_with_purport += 1
            if synonyms:
                mantras_with_synonyms += 1
            
            # Track which mantras we have
            if mantra_numbers:
                for mnum in mantra_numbers:
                    if mnum == 'invocation':
                        has_invocation = True
                        covered_mantras.add('invocation')
                    elif mnum.isdigit():
                        covered_mantras.add(mnum)  # Keep as string
                    
            mantra_details.append({
                'mantra_number': mantra_number,
                'mantra_numbers': mantra_numbers,
                'has_sanskrit': bool(sanskrit),
                'has_translation': bool(translation),
                'has_purport': bool(purport),
                'has_synonyms': bool(synonyms),
                'content_score': sum([bool(sanskrit), bool(translation), bool(purport), bool(synonyms)]),
                'content_length': len(translation) + len(purport)
            })
        
        # Calculate expected coverage
        expected_mantras = get_expected_mantras()
        individual_mantra_count = len(covered_mantras)
        
        # Find missing mantras
        expected_set = set(['invocation'] + [str(i) for i in range(1, 19)])  # invocation + mantras 1-18 as strings
        missing_mantras = expected_set - covered_mantras
        
        # Determine status
        if mantra_count == 0:
            status = 'EMPTY'
        elif individual_mantra_count < len(expected_mantras) * 0.8:  # Less than 80% of expected mantras
            status = 'INCOMPLETE'
        elif mantras_with_translation < mantra_count * 0.9:  # Less than 90% have translations
            status = 'POOR_QUALITY'
        else:
            status = 'COMPLETE'
        
        return {
            'exists': True,
            'title': title,
            'mantras': mantra_count,
            'expected_mantras': len(expected_mantras),
            'individual_mantra_count': individual_mantra_count,
            'covered_mantras': sorted([m for m in covered_mantras if isinstance(m, int)] + 
                                    [m for m in covered_mantras if m == 'invocation']),
            'missing_mantras': sorted([m for m in missing_mantras if isinstance(m, int)] + 
                                    [m for m in missing_mantras if m == 'invocation']),
            'has_invocation': has_invocation,
            'completion_percentage': (individual_mantra_count / len(expected_mantras) * 100) if expected_mantras else 0,
            'mantras_with_sanskrit': mantras_with_sanskrit,
            'mantras_with_translation': mantras_with_translation,
            'mantras_with_purport': mantras_with_purport,
            'mantras_with_synonyms': mantras_with_synonyms,
            'status': status,
            'mantra_details': mantra_details,
            'content_quality': {
                'sanskrit_coverage': mantras_with_sanskrit / mantra_count if mantra_count > 0 else 0,
                'translation_coverage': mantras_with_translation / mantra_count if mantra_count > 0 else 0,
                'purport_coverage': mantras_with_purport / mantra_count if mantra_count > 0 else 0,
                'synonyms_coverage': mantras_with_synonyms / mantra_count if mantra_count > 0 else 0
            }
        }
        
    except Exception as e:
        return {
            'exists': True,
            'error': str(e),
            'status': 'ERROR'
        }

def get_expected_mantras() -> List:
    """Return expected mantras for Śrī Īśopaniṣad"""
    return ['invocation'] + list(range(1, 19))  # Invocation + Mantras 1-18

def get_mantra_titles():
    """Return standard mantra titles/descriptions"""
    return {
        'invocation': "Invocation - The Complete Whole",
        1: "Mantra 1 - Everything belongs to the Lord",
        2: "Mantra 2 - Live for hundreds of years by working",
        3: "Mantra 3 - The killer of the soul",
        4: "Mantra 4 - The Lord is swifter than the mind",
        5: "Mantra 5 - The Lord walks and does not walk",
        6: "Mantra 6 - Seeing everything in relation to the Lord",
        7: "Mantra 7 - True knowledge removes illusion",
        8: "Mantra 8 - The greatest Personality of Godhead",
        9: "Mantra 9 - Culture of nescience leads to darkness",
        10: "Mantra 10 - Different results from knowledge and nescience",
        11: "Mantra 11 - Transcending birth and death",
        12: "Mantra 12 - Worship of demigods vs the Supreme",
        13: "Mantra 13 - Worshiping the supreme vs non-supreme",
        14: "Mantra 14 - Knowing both material and spiritual",
        15: "Mantra 15 - Prayer to see the real face of the Lord",
        16: "Mantra 16 - The Lord as the primeval philosopher",
        17: "Mantra 17 - Merging with air and remembering sacrifices",
        18: "Mantra 18 - Final prayer for guidance and forgiveness"
    }

def main():
    """Main analysis function"""
    print("=" * 80)
    print("ŚRĪ ĪŚOPANIṢAD SCRAPING COMPLETION ANALYSIS")
    print("=" * 80)
    
    expected_mantras = get_expected_mantras()
    expected_total_mantras = len(expected_mantras)
    mantra_titles = get_mantra_titles()
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"Expected: {expected_total_mantras} mantras (1 invocation + 18 mantras)")
    print("\n" + "=" * 80)
    
    analysis = analyze_isopanisad_data()
    
    if not analysis['exists']:
        print("\n❌ DATA FILE NOT FOUND!")
        print("Expected file: data_iso/raw/sri_isopanisad_complete.json")
        print("Please run the scraper first: python sri_isopanisad_scraper.py")
        return
    
    if 'error' in analysis:
        print(f"\n❌ ERROR ANALYZING DATA: {analysis['error']}")
        return
    
    print(f"\n📖 ŚRĪĪ ĪŚOPANIṢAD ANALYSIS:")
    print(f"   Title: {analysis['title']}")
    print(f"   📊 Total Mantras: {analysis['mantras']}")
    print(f"   📊 Individual Mantras: {analysis['individual_mantra_count']}/{expected_total_mantras} ({analysis['completion_percentage']:.1f}%)")
    print(f"   Status: {'✅ ' if analysis['status'] == 'COMPLETE' else '⚠️ ' if analysis['status'] in ['INCOMPLETE', 'POOR_QUALITY'] else '❌ '}{analysis['status']}")
    
    # Show missing mantras if any
    if analysis.get('missing_mantras'):
        missing = analysis['missing_mantras']
        print(f"\n⚠️  MISSING MANTRAS: {len(missing)}")
        for mantra in missing:
            if mantra == 'invocation':
                print(f"   • Invocation: {mantra_titles.get('invocation', 'Invocation')}")
            else:
                print(f"   • Mantra {mantra}: {mantra_titles.get(mantra, f'Mantra {mantra}')}")
    
    # Show content quality
    if 'content_quality' in analysis:
        quality = analysis['content_quality']
        print(f"\n📊 CONTENT QUALITY:")
        print(f"   Sanskrit: {quality['sanskrit_coverage']*100:.1f}% ({analysis['mantras_with_sanskrit']}/{analysis['mantras']})")
        print(f"   Translation: {quality['translation_coverage']*100:.1f}% ({analysis['mantras_with_translation']}/{analysis['mantras']})")
        print(f"   Purport: {quality['purport_coverage']*100:.1f}% ({analysis['mantras_with_purport']}/{analysis['mantras']})")
        print(f"   Synonyms: {quality['synonyms_coverage']*100:.1f}% ({analysis['mantras_with_synonyms']}/{analysis['mantras']})")
    
    # Show mantra details
    print(f"\n📋 DETAILED MANTRA BREAKDOWN:")
    for detail in analysis['mantra_details']:
        mantra_id = detail['mantra_number']
        score = detail['content_score']
        length = detail['content_length']
        
        status_icon = "✅" if score >= 3 else "⚠️" if score >= 2 else "❌"
        
        print(f"   {status_icon} {mantra_id}: Content Score {score}/4, Length: {length:,} chars")
        
        parts = []
        if detail['has_sanskrit']: parts.append("Sanskrit")
        if detail['has_translation']: parts.append("Translation")
        if detail['has_purport']: parts.append("Purport")
        if detail['has_synonyms']: parts.append("Synonyms")
        
        if parts:
            print(f"      Has: {', '.join(parts)}")
        else:
            print(f"      ⚠️ No content found!")
    
    print("\n" + "=" * 80)
    print("📈 FINAL STATISTICS:")
    print("=" * 80)
    
    if analysis['status'] == 'COMPLETE':
        print("🎉 STATUS: FULLY COMPLETE! All mantras have been successfully scraped.")
    elif analysis['completion_percentage'] >= 90:
        print(f"⚡ STATUS: NEARLY COMPLETE! {analysis['completion_percentage']:.1f}% done.")
    elif analysis['completion_percentage'] >= 70:
        print(f"🔄 STATUS: GOOD PROGRESS! {analysis['completion_percentage']:.1f}% done.")
    else:
        print(f"🚧 STATUS: IN PROGRESS! {analysis['completion_percentage']:.1f}% done.")
    
    # Quality assessment
    if analysis['mantras'] > 0:
        translation_rate = analysis['mantras_with_translation'] / analysis['mantras']
        purport_rate = analysis['mantras_with_purport'] / analysis['mantras']
        
        print(f"\n📊 CONTENT QUALITY ASSESSMENT:")
        if translation_rate > 0.95 and purport_rate > 0.90:
            print("🌟 EXCELLENT: High-quality content with comprehensive translations and purports")
        elif translation_rate > 0.85 and purport_rate > 0.70:
            print("✅ GOOD: Solid content quality with most mantras having translations and purports")
        elif translation_rate > 0.70:
            print("⚠️  FAIR: Adequate translations, but some purports may be missing")
        else:
            print("🔴 POOR: Significant content missing - translations and purports incomplete")
    
    # Check for invocation specifically
    if analysis.get('has_invocation'):
        print(f"\n✅ INVOCATION: Present")
    else:
        print(f"\n❌ INVOCATION: Missing - this is essential for Śrī Īśopaniṣad")
    
    # Recommendations
    if analysis['status'] != 'COMPLETE':
        print(f"\n💡 RECOMMENDATIONS:")
        if analysis.get('missing_mantras'):
            print(f"   • Re-run the scraper to capture missing mantras")
        if analysis['mantras_with_translation'] < analysis['mantras'] * 0.9:
            print(f"   • Check extraction logic for translation sections")
        if analysis['mantras_with_purport'] < analysis['mantras'] * 0.8:
            print(f"   • Verify purport extraction from HTML structure")
        if not analysis.get('has_invocation'):
            print(f"   • Ensure invocation page is included in URL discovery")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
