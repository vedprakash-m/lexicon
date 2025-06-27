#!/usr/bin/env python3
"""
Comprehensive analysis tool for Bhagavad Gita scraping completion
Analyzes all scraped data to determine completeness of all 18 chapters
"""

import json
import os
from typing import Dict

def analyze_chapter_file(chapter_num: int) -> Dict:
    """Analyze a single chapter file for completeness"""
    filename = f'data_bg/raw/chapters/chapter_{chapter_num:02d}.json'
    
    if not os.path.exists(filename):
        return {
            'chapter_number': chapter_num,
            'exists': False,
            'verses': 0,
            'status': 'MISSING'
        }
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        verses = data.get('verses', [])
        verse_count = len(verses)
        chapter_title = data.get('title', f'Chapter {chapter_num}')
        
        # Check content quality
        verses_with_sanskrit = 0
        verses_with_translation = 0
        verses_with_purport = 0
        verses_with_synonyms = 0
        
        # Track individual verses covered (accounting for joint verses)
        covered_verse_numbers = set()
        verse_details = []
        joint_verses = []
        
        for verse in verses:
            sanskrit = verse.get('sanskrit_verse', '').strip()
            translation = verse.get('translation', '').strip()
            purport = verse.get('purport', '').strip()
            synonyms = verse.get('synonyms', '').strip()
            verse_number = verse.get('verse_number', '')
            verse_numbers = verse.get('verse_numbers', [])
            
            if sanskrit:
                verses_with_sanskrit += 1
            if translation:
                verses_with_translation += 1
            if purport:
                verses_with_purport += 1
            if synonyms:
                verses_with_synonyms += 1
            
            # Handle joint verses (e.g., 1.16-18)
            if verse_numbers:
                # This is a joint verse entry
                for vnum_str in verse_numbers:
                    try:
                        # Extract verse number from format like "1.16" -> 16
                        if '.' in vnum_str:
                            vnum = int(vnum_str.split('.')[-1])
                            covered_verse_numbers.add(vnum)
                    except (ValueError, IndexError):
                        pass
                joint_verses.append({
                    'verse_number': verse_number,
                    'verse_numbers': verse_numbers,
                    'covers_individual_verses': len(verse_numbers)
                })
            else:
                # Single verse entry
                if verse_number:
                    # Extract just the verse number (e.g., "1.16" -> 16)
                    try:
                        if '.' in verse_number:
                            vnum = int(verse_number.split('.')[-1])
                            covered_verse_numbers.add(vnum)
                    except (ValueError, IndexError):
                        pass
                
            verse_details.append({
                'verse_number': verse_number,
                'verse_numbers': verse_numbers,
                'has_sanskrit': bool(sanskrit),
                'has_translation': bool(translation),
                'has_purport': bool(purport),
                'has_synonyms': bool(synonyms),
                'content_score': sum([bool(sanskrit), bool(translation), bool(purport), bool(synonyms)]),
                'is_joint_verse': bool(verse_numbers)
            })
        
        # Calculate actual individual verse coverage
        expected_verse_count = get_expected_verse_count(chapter_num)
        individual_verse_count = len(covered_verse_numbers)
        
        # Find missing verses
        expected_verses = set(range(1, expected_verse_count + 1))
        missing_verses = expected_verses - covered_verse_numbers
        
        # Determine status based on individual verse coverage
        if verse_count == 0:
            status = 'EMPTY'
        elif individual_verse_count < expected_verse_count * 0.8:  # Less than 80% of expected individual verses
            status = 'INCOMPLETE'
        elif verses_with_translation < verse_count * 0.9:  # Less than 90% have translations
            status = 'POOR_QUALITY'
        else:
            status = 'COMPLETE'
        
        return {
            'chapter_number': chapter_num,
            'exists': True,
            'title': chapter_title,
            'verses': verse_count,
            'expected_verses': expected_verse_count,
            'individual_verse_count': individual_verse_count,
            'covered_verse_numbers': sorted(list(covered_verse_numbers)),
            'missing_verses': sorted(list(missing_verses)),
            'joint_verses': joint_verses,
            'completion_percentage': (individual_verse_count / expected_verse_count * 100) if expected_verse_count > 0 else 0,
            'verses_with_sanskrit': verses_with_sanskrit,
            'verses_with_translation': verses_with_translation,
            'verses_with_purport': verses_with_purport,
            'verses_with_synonyms': verses_with_synonyms,
            'status': status,
            'verse_details': verse_details,
            'content_quality': {
                'sanskrit_coverage': verses_with_sanskrit / verse_count if verse_count > 0 else 0,
                'translation_coverage': verses_with_translation / verse_count if verse_count > 0 else 0,
                'purport_coverage': verses_with_purport / verse_count if verse_count > 0 else 0,
                'synonyms_coverage': verses_with_synonyms / verse_count if verse_count > 0 else 0
            }
        }
        
    except Exception as e:
        return {
            'chapter_number': chapter_num,
            'exists': True,
            'error': str(e),
            'status': 'ERROR'
        }

def get_expected_verse_count(chapter_num: int) -> int:
    """Return expected verse counts for each chapter of Bhagavad Gita"""
    expected_counts = {
        1: 46,   # Observing the Armies on the Battlefield of Kurukṣetra (corrected from 47)
        2: 72,   # Contents of the Gītā Summarized
        3: 43,   # Karma-yoga
        4: 42,   # Transcendental Knowledge
        5: 29,   # Karma-yoga – Action in Kṛṣṇa Consciousness
        6: 47,   # Dhyāna-yoga
        7: 30,   # Knowledge of the Absolute
        8: 28,   # Attaining the Supreme
        9: 34,   # The Most Confidential Knowledge
        10: 42,  # The Opulence of the Absolute
        11: 55,  # The Universal Form
        12: 20,  # Devotional Service
        13: 35,  # Nature, the Enjoyer and Consciousness
        14: 27,  # The Three Modes of Material Nature
        15: 20,  # The Yoga of the Supreme Person
        16: 24,  # The Divine and Demoniac Natures
        17: 28,  # The Divisions of Faith
        18: 78   # Conclusion – The Perfection of Renunciation
    }
    return expected_counts.get(chapter_num, 40)  # Default to 40 if unknown

def get_chapter_titles():
    """Return standard chapter titles"""
    return {
        1: "Observing the Armies on the Battlefield of Kurukṣetra",
        2: "Contents of the Gītā Summarized", 
        3: "Karma-yoga",
        4: "Transcendental Knowledge",
        5: "Karma-yoga – Action in Kṛṣṇa Consciousness",
        6: "Dhyāna-yoga",
        7: "Knowledge of the Absolute",
        8: "Attaining the Supreme",
        9: "The Most Confidential Knowledge",
        10: "The Opulence of the Absolute",
        11: "The Universal Form",
        12: "Devotional Service",
        13: "Nature, the Enjoyer and Consciousness",
        14: "The Three Modes of Material Nature",
        15: "The Yoga of the Supreme Person",
        16: "The Divine and Demoniac Natures",
        17: "The Divisions of Faith",
        18: "Conclusion – The Perfection of Renunciation"
    }

def analyze_complete_file():
    """Analyze the complete bhagavad_gita_complete.json file"""
    filename = 'data_bg/raw/bhagavad_gita_complete.json'
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_chapters = len(data)
        total_verses = 0
        
        for chapter_data in data.values():
            if isinstance(chapter_data, dict) and 'verses' in chapter_data:
                total_verses += len(chapter_data['verses'])
        
        return {
            'exists': True,
            'total_chapters': total_chapters,
            'total_verses': total_verses
        }
        
    except Exception as e:
        return {
            'exists': True,
            'error': str(e)
        }

def main():
    """Main analysis function"""
    print("=" * 80)
    print("BHAGAVAD GITA SCRAPING COMPLETION ANALYSIS")
    print("=" * 80)
    
    expected_chapters = 18
    expected_total_verses = sum(get_expected_verse_count(i) for i in range(1, 19))
    chapter_titles = get_chapter_titles()
    
    complete_chapters = 0
    total_verses_found = 0
    total_sanskrit_verses = 0
    total_translations = 0
    total_purports = 0
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"Expected: {expected_chapters} chapters, {expected_total_verses} verses")
    print("\n" + "=" * 80)
    
    chapter_analyses = []
    
    for chapter_num in range(1, 19):
        analysis = analyze_chapter_file(chapter_num)
        chapter_analyses.append(analysis)
        
        expected_verses = get_expected_verse_count(chapter_num)
        expected_title = chapter_titles.get(chapter_num, f'Chapter {chapter_num}')
        
        print(f"\n📖 CHAPTER {chapter_num}:")
        print(f"   Expected: {expected_title}")
        
        if analysis['exists'] and 'error' not in analysis:
            actual_title = analysis.get('title', 'No title')
            verses_found = analysis['verses']
            status = analysis['status']
            
            total_verses_found += verses_found
            
            if 'verses_with_sanskrit' in analysis:
                total_sanskrit_verses += analysis['verses_with_sanskrit']
                total_translations += analysis['verses_with_translation']
                total_purports += analysis['verses_with_purport']
            
            print(f"   Actual: {actual_title}")
            print(f"   📊 Verse Entries: {verses_found} | Individual Verses: {analysis['individual_verse_count']}/{expected_verses} ({analysis['completion_percentage']:.1f}%)")
            
            # Show joint verses if any
            if analysis.get('joint_verses'):
                joint_count = len(analysis['joint_verses'])
                total_individual_in_joints = sum(j['covers_individual_verses'] for j in analysis['joint_verses'])
                print(f"   🔗 Joint Verses: {joint_count} entries covering {total_individual_in_joints} individual verses")
                for joint in analysis['joint_verses'][:3]:  # Show first 3 as examples
                    verse_range = f"{min(joint['verse_numbers'])}-{max(joint['verse_numbers'])}" if len(joint['verse_numbers']) > 1 else str(joint['verse_numbers'][0])
                    print(f"      • {joint['verse_number']} (covers {verse_range})")
                if len(analysis['joint_verses']) > 3:
                    print(f"      ... and {len(analysis['joint_verses']) - 3} more")
            
            if status == 'COMPLETE':
                complete_chapters += 1
                print("   Status: ✅ COMPLETE")
            elif status == 'INCOMPLETE':
                print("   Status: ⚠️  INCOMPLETE (missing verses)")
                if analysis.get('missing_verses'):
                    missing = analysis['missing_verses']
                    if len(missing) <= 10:
                        print(f"      Missing individual verses: {missing}")
                    else:
                        print(f"      Missing individual verses: {missing[:5]}...{missing[-5:]} ({len(missing)} total)")
            elif status == 'POOR_QUALITY':
                print("   Status: ⚠️  POOR QUALITY (missing content)")
            else:
                print(f"   Status: ❌ {status}")
            
            # Show content quality
            if 'content_quality' in analysis:
                quality = analysis['content_quality']
                print(f"   Content Quality:")
                print(f"     Sanskrit: {quality['sanskrit_coverage']*100:.1f}%")
                print(f"     Translation: {quality['translation_coverage']*100:.1f}%")
                print(f"     Purport: {quality['purport_coverage']*100:.1f}%")
                print(f"     Synonyms: {quality['synonyms_coverage']*100:.1f}%")
        
        elif 'error' in analysis:
            print(f"   Status: ❌ ERROR: {analysis['error']}")
        else:
            print(f"   Status: ❌ FILE MISSING")
    
    # Calculate accurate statistics based on individual verses
    total_individual_verses = sum(analysis.get('individual_verse_count', 0) for analysis in chapter_analyses if analysis['exists'])
    total_missing_verses = sum(len(analysis.get('missing_verses', [])) for analysis in chapter_analyses if analysis['exists'])
    total_joint_entries = sum(len(analysis.get('joint_verses', [])) for analysis in chapter_analyses if analysis['exists'])
    
    print("\n" + "=" * 80)
    print("📈 FINAL STATISTICS (CORRECTED FOR JOINT VERSES):")
    print("=" * 80)
    print(f"Complete chapters: {complete_chapters}/{expected_chapters} ({complete_chapters/expected_chapters*100:.1f}%)")
    print(f"Individual verses found: {total_individual_verses}/{expected_total_verses} ({total_individual_verses/expected_total_verses*100:.1f}%)")
    print(f"Missing individual verses: {total_missing_verses}")
    print(f"Joint verse entries: {total_joint_entries}")
    print(f"Total verse entries: {total_verses_found}")
    print(f"Verses with Sanskrit: {total_sanskrit_verses:,}")
    print(f"Verses with Translation: {total_translations:,}")
    print(f"Verses with Purport: {total_purports:,}")
    
    # Analyze complete file
    complete_analysis = analyze_complete_file()
    if complete_analysis:
        if 'error' not in complete_analysis:
            print(f"Complete file verses: {complete_analysis['total_verses']:,}")
        else:
            print(f"Complete file error: {complete_analysis['error']}")
    else:
        print("Complete file: Not found")
    
    # Overall completion status
    if complete_chapters == expected_chapters:
        print("\n🎉 STATUS: FULLY COMPLETE! All chapters have been successfully scraped.")
    elif complete_chapters >= 15:
        print(f"\n⚡ STATUS: NEARLY COMPLETE! {complete_chapters} of {expected_chapters} chapters done.")
    elif complete_chapters >= 10:
        print(f"\n🔄 STATUS: GOOD PROGRESS! {complete_chapters} of {expected_chapters} chapters done.")
    else:
        print(f"\n🚧 STATUS: IN PROGRESS! {complete_chapters} of {expected_chapters} chapters done.")
    
    # Quality assessment
    if total_verses_found > 0:
        translation_rate = total_translations / total_verses_found
        purport_rate = total_purports / total_verses_found
        
        print(f"\n📊 CONTENT QUALITY ASSESSMENT:")
        if translation_rate > 0.95 and purport_rate > 0.90:
            print("🌟 EXCELLENT: High-quality content with comprehensive translations and purports")
        elif translation_rate > 0.85 and purport_rate > 0.70:
            print("✅ GOOD: Solid content quality with most verses having translations and purports")
        elif translation_rate > 0.70:
            print("⚠️  FAIR: Adequate translations, but some purports may be missing")
        else:
            print("🔴 POOR: Significant content missing - translations and purports incomplete")
    
    # Show any problematic chapters
    problem_chapters = [ch for ch in chapter_analyses if ch['status'] in ['INCOMPLETE', 'POOR_QUALITY', 'ERROR', 'EMPTY']]
    if problem_chapters:
        print("\n⚠️  CHAPTERS NEEDING ATTENTION:")
        for ch in problem_chapters:
            if ch.get('missing_verses'):
                missing_count = len(ch['missing_verses'])
                print(f"   Chapter {ch['chapter_number']}: {ch['status']} - {missing_count} missing verses")
                if missing_count <= 20:  # Show details for chapters with few missing verses
                    print(f"      Missing: {ch['missing_verses']}")
            else:
                print(f"   Chapter {ch['chapter_number']}: {ch['status']}")
    
    # Summary of chapters with missing verses (after correcting for joint verses)
    chapters_with_missing = [ch for ch in chapter_analyses if ch.get('missing_verses')]
    if chapters_with_missing:
        print(f"\n📋 DETAILED MISSING VERSE ANALYSIS:")
        print(f"   Chapters with missing verses: {len(chapters_with_missing)}")
        for ch in chapters_with_missing:
            missing_count = len(ch['missing_verses'])
            completion = ch['completion_percentage']
            print(f"   • Chapter {ch['chapter_number']}: {missing_count} missing ({completion:.1f}% complete)")
            if missing_count <= 10:
                print(f"     Missing verses: {ch['missing_verses']}")
    else:
        print(f"\n🎉 ALL INDIVIDUAL VERSES ARE PRESENT!")
        print(f"   The apparent 'missing' verses were actually part of joint verse entries.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
