# Generated manually for performance optimization
# Phase 1: Add database indexes for frequently queried fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0072_update_project_location'),
    ]

    operations = [
        # Add indexes to ProjectClass
        migrations.AddIndex(
            model_name='projectclass',
            index=models.Index(fields=['parent'], name='idx_projectclass_parent'),
        ),
        migrations.AddIndex(
            model_name='projectclass',
            index=models.Index(fields=['defaultProgrammer'], name='idx_projectclass_programmer'),
        ),
        migrations.AddIndex(
            model_name='projectclass',
            index=models.Index(fields=['path'], name='idx_projectclass_path'),
        ),
        migrations.AddIndex(
            model_name='projectclass',
            index=models.Index(fields=['forCoordinatorOnly'], name='idx_projectclass_coordinator'),
        ),
        
        # Add indexes to ClassFinancial
        migrations.AddIndex(
            model_name='classfinancial',
            index=models.Index(fields=['year'], name='idx_classfinancial_year'),
        ),
        migrations.AddIndex(
            model_name='classfinancial',
            index=models.Index(fields=['forFrameView'], name='idx_classfinancial_frameview'),
        ),
        migrations.AddIndex(
            model_name='classfinancial',
            index=models.Index(fields=['classRelation'], name='idx_classfinancial_class'),
        ),
        # Composite index for common query pattern
        migrations.AddIndex(
            model_name='classfinancial',
            index=models.Index(fields=['classRelation', 'year', 'forFrameView'], name='idx_classfinancial_composite'),
        ),
        
        # Add indexes to Project for performance (frequently joined in FinancialSumSerializer)
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['programmed'], name='idx_project_programmed'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['projectClass'], name='idx_project_class'),
        ),
        
        # Add indexes to ProjectFinancial
        migrations.AddIndex(
            model_name='projectfinancial',
            index=models.Index(fields=['year'], name='idx_projectfinancial_year'),
        ),
        migrations.AddIndex(
            model_name='projectfinancial',
            index=models.Index(fields=['forFrameView'], name='idx_projectfinancial_frameview'),
        ),
        
        # Add indexes to ProjectLocation (for hierarchical queries)
        migrations.AddIndex(
            model_name='projectlocation',
            index=models.Index(fields=['parent'], name='idx_projectlocation_parent'),
        ),
        migrations.AddIndex(
            model_name='projectlocation',
            index=models.Index(fields=['parentClass'], name='idx_projloc_parentclass'),
        ),
    ]

