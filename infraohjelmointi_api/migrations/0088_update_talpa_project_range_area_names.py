from django.db import migrations


def update_project_range_area_names(apps, schema_editor):
    """Update project number range area names as requested by customer"""
    TalpaProjectNumberRange = apps.get_model('infraohjelmointi_api', 'TalpaProjectNumberRange')
    
    # Update project range area names
    updates = [
        {
            'budgetAccount': '8 01 03 01',
            'old_area': 'Muu esirakentaminen (MuuEsir.)',
            'new_area': 'Muu esirakentaminen'
        },
        {
            'budgetAccount': '8 08 01 08',
            'old_area': 'Malmi (kenttä)',
            'new_area': 'Malminkenttä'
        },
        {
            'budgetAccount': '8 10 04 01',
            'old_area': 'LHR, liittyvä esirakentaminen',
            'new_area': 'Länsiratikat, liittyvä esir.'
        },
    ]
    
    for update in updates:
        # Find ranges with matching budgetAccount
        ranges = TalpaProjectNumberRange.objects.filter(
            budgetAccount=update['budgetAccount']
        )
        
        for r in ranges:
            # Check if area contains the old name (or matches exactly)
            if update['old_area'] in r.area:
                r.area = update['new_area']
                r.save()


def reverse_update_project_range_area_names(apps, schema_editor):
    """Reverse the project range area name updates"""
    TalpaProjectNumberRange = apps.get_model('infraohjelmointi_api', 'TalpaProjectNumberRange')
    
    reversals = [
        {
            'budgetAccount': '8 01 03 01',
            'old_area': 'Muu esirakentaminen',
            'new_area': 'Muu esirakentaminen (MuuEsir.)'
        },
        {
            'budgetAccount': '8 08 01 08',
            'old_area': 'Malminkenttä',
            'new_area': 'Malmi (kenttä)'
        },
        {
            'budgetAccount': '8 10 04 01',
            'old_area': 'Länsiratikat, liittyvä esir.',
            'new_area': 'LHR, liittyvä esirakentaminen'
        },
    ]
    
    for reversal in reversals:
        ranges = TalpaProjectNumberRange.objects.filter(
            budgetAccount=reversal['budgetAccount']
        )
        for r in ranges:
            if r.area == reversal['old_area']:
                r.area = reversal['new_area']
                r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0087_merge_construction_procurement_project_types'),
    ]

    operations = [
        migrations.RunPython(update_project_range_area_names, reverse_update_project_range_area_names),
    ]
