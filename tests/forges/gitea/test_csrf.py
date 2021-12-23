""" Test for Gitea CSRF parser"""
# Interface ---  API-space federation for software forges
# Copyright © 2021 Aravinth Manivannan <realaravinth@batsense.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from interface.forges.gitea import ParseCSRFGiteaForm

from tests.forges.gitea.test_utils import PAGE1, CSRF_TOKEN_2, CSRF_TOKEN, PAGE2


def test_csrf_parser():
    # return when first token is found
    parser = ParseCSRFGiteaForm()
    parser.feed(PAGE1)
    assert parser.token == CSRF_TOKEN

    # Token is already found, new parsing and searching should return immediately
    # without any processing/changing tokens
    parser = ParseCSRFGiteaForm()
    parser.token = CSRF_TOKEN_2
    parser.feed(PAGE1)
    assert parser.token == CSRF_TOKEN_2

    # value attribute encountered early, does attribute caching work?
    parser = ParseCSRFGiteaForm()
    parser.feed(PAGE2)
    assert parser.token == CSRF_TOKEN
