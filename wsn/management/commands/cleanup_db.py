import logging

# Django
from django.core.management.base import BaseCommand
from django.db import transaction

# Project
from wsn.models import Frame, Metadata


logger = logging.getLogger(__name__)

DELETE = [
    '4g_uio_test',
    'fw-test',
    'fw-WS100-Finse',
    'iridium_uio_test',
    'JH_test@UIO',
    'node_id',
    'remote_cs',
    'sw-new1',
    'sw-test',
    'test_4g_1',
    'test_4g_2',
    'test_4g_3',
    'test_onewire',
    'thehill',
    'uio-ws100test',
    'uw-iridium_test',
    'uw-loratest',
    'uw-sd_testing',
    'uw-test',
    'uw-test1',
    'uw-test10',
    'uw-test2',
    'uw-test3',
    'uw-test4',
    'uw-test6',
    'uw-test7',
    'uw-test8',
    'uw-test9',
    'uw-testi2c',
    'uw-test_precip',
    'uw-xbee_test',
    'WS100-Finse',
]

RENAME = {
    'f-finselvi_dis': 'fw-finselvi_dis',
    'fw-marsh_tab': 'fw-mwtable',
    'fw-middalselvi_2': 'fw-middalselvi',
    'fw-midelvi-2': 'fw-middalselvi',
    'fw-mwtab': 'fw-mwtable',
    'FW-TheHill': 'fw-008',
    'fw-thomas_statio': 'fw-001',
    'marsh_wtable': 'fw-mwtable',
    'sw-002': 'sw-200',
    'sw-004': 'sw-240',
    'sw-006': 'sw-220',
    'sw-009': 'sw-230',
}

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)

    def __count(self, msg):
        n = Metadata.objects.count()
        m = Frame.objects.count()
        logger.info(f'{msg}: {n} metadatas and {m} frames')

    def __delete(self, queryset):
        n, detail = queryset.delete()
        logger.info(f'Objects deleted {detail}')

    def handle(self, *arg, **kw):
        save = kw['save']
        if not save:
            logger.info('The changes will not be saved')

        self.__count('Before')

        abort_message = 'Abort the transaction'
        try:
            with transaction.atomic():
                # Delete
                self.__delete(Frame.objects.filter(metadata__name__in=DELETE))
                self.__delete(Metadata.objects.filter(name__in=DELETE))

                # Rename
                for metadata in Metadata.objects.filter(name__in=RENAME.keys()):
                    new_name = RENAME[metadata.name]
                    #logger.info(f'Rename metadata pk={metadata.pk} from {metadata.name} to {new_name}')
                    metadata2 = Metadata.objects.filter(name=new_name, tags=metadata.tags).first()
                    if metadata2 is not None:
                        n = Frame.objects.filter(metadata=metadata).update(metadata=metadata2)
                        logger.info(f'{n} frames moved from metadata {metadata.pk} to {metadata2.pk}')
                        metadata.delete()
                    else:
                        metadata.name = new_name
                        metadata.save(update_fields=['name'])

                # Count
                self.__count('After ')

                # Raise an exception to abort the transaction
                if not save:
                    raise RuntimeError(abort_message)
        except RuntimeError as excp:
            if str(excp) != abort_message: # This was unexpected
                raise

            logger.info(abort_message)

        self.__count('Final ')
