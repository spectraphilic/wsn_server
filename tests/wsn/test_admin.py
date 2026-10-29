# Django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

# Requirements
import pytest

# Project
from wsn.models import ImportFile


@pytest.fixture
def staff(db):
    User = get_user_model()
    return User.objects.create_user('staff', password='x', is_staff=True)


def test_admin_shows_importfile_link(client, staff):
    staff.user_permissions.add(Permission.objects.get(codename='view_frame'))
    client.force_login(staff)
    for url in (reverse('admin:index'), reverse('admin:wsn_frame_changelist')):
        response = client.get(url)
        assert response.status_code == 200
        assert reverse('admin_importfile_list') in response.content.decode()


def test_importfile_list(client, staff):
    ImportFile.objects.create(name='eton2', path='2026/10/x.dat.xz')
    client.force_login(staff)
    response = client.get(reverse('admin_importfile_list'))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'eton2' in content
    assert '2026/10/x.dat.xz' in content
    assert 'pending' in content


def test_importfile_list_pagination(client, staff):
    ImportFile.objects.bulk_create(
        ImportFile(name=f'n{i:03}', path='x') for i in range(250)
    )
    client.force_login(staff)

    response = client.get(reverse('admin_importfile_list'))
    page = response.context['page']
    assert page.number == 1
    assert len(page.object_list) == 100
    assert page.paginator.num_pages == 3

    response = client.get(reverse('admin_importfile_list'), {'page': '2'})
    assert response.context['page'].number == 2

    response = client.get(reverse('admin_importfile_list'), {'page': 'bogus'})
    assert response.context['page'].number == 1

    response = client.get(reverse('admin_importfile_list'), {'page': '99'})
    assert response.context['page'].number == 3


def test_importfile_list_login_required(client):
    response = client.get(reverse('admin_importfile_list'))
    assert response.status_code == 302


def test_importfile_list_filters(client, staff):
    ImportFile.objects.create(name='eton2', path='eton2.xz',
                              status=ImportFile.Status.DONE)
    ImportFile.objects.create(name='licor_myr2', path='pending.xz')
    ImportFile.objects.create(name='licor_myr2', path='error.xz',
                              status=ImportFile.Status.ERROR)
    client.force_login(staff)
    url = reverse('admin_importfile_list')

    response = client.get(url, {'name': 'licor_myr2'})
    content = response.content.decode()
    assert 'pending.xz' in content
    assert 'error.xz' in content
    assert 'eton2.xz' not in content

    response = client.get(url, {'status': 'pending'})
    content = response.content.decode()
    assert 'pending.xz' in content
    assert 'error.xz' not in content
    assert 'eton2.xz' not in content

    # Both filters combine
    response = client.get(url, {'name': 'licor_myr2', 'status': 'error'})
    content = response.content.decode()
    assert 'error.xz' in content
    assert 'pending.xz' not in content

    # Unknown status is ignored, all rows shown
    response = client.get(url, {'status': 'bogus'})
    assert 'eton2.xz' in response.content.decode()
    assert 'pending.xz' in response.content.decode()


def test_importfile_list_pager_keeps_filters(client, staff):
    ImportFile.objects.bulk_create(
        ImportFile(name='n1', path=f'n1_{i:03}.xz') for i in range(150)
    )
    ImportFile.objects.bulk_create(
        ImportFile(name='n2', path=f'n2_{i:03}.xz') for i in range(150)
    )
    client.force_login(staff)
    url = reverse('admin_importfile_list')

    response = client.get(url, {'name': 'n1'})
    content = response.content.decode()
    assert 'n2_000.xz' not in content
    # The pager links keep the active filter
    assert 'name=n1&amp;page=2' in content

    response = client.get(url, {'name': 'n1', 'page': '2'})
    assert 'n1_149.xz' in response.content.decode()


def test_importfile_list_pager_above_table(client, staff):
    ImportFile.objects.bulk_create(
        ImportFile(name=f'n{i:03}', path='x') for i in range(250)
    )
    client.force_login(staff)
    response = client.get(reverse('admin_importfile_list'))
    content = response.content.decode()
    assert content.index('Page 1 / 3') < content.index('<table>')
