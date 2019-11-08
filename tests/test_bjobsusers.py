# encoding: utf-8

import os
import subprocess

import pandas as pd

import pytest

from subscript.bjobsusers import bjobsusers


def fake_bjobs(status):
    return "foobar 3*computenode1\nfoobert 1*computenode2\nfoobar 8*computenode3"


def bjobs_errors(status):
    # Example error message from bjobs
    return "LIM not responding"


class FakeFinger(object):
    def __init__(self, name):
        self._name = name

    def __call__(self, username):
        result = "Login: {}          Name: " + self._name
        return subprocess.check_output(("echo", result)).decode("utf-8")


def test_real_bjobs():
    """Test the real bjobs command. Can only be expected to
    work on production system interactively"""
    jobs_df = bjobsusers.get_jobs("RUN", bjobsusers.call_bjobs)
    if jobs_df.empty:
        pytest.skip("bjobs command not available, skipping test")
    assert isinstance(jobs_df, pd.DataFrame)
    assert "ncpu" in jobs_df.columns
    assert "user" in jobs_df.index.name

    # The real bjobs is allowed to return empty..
    if not jobs_df.empty:
        assert len(jobs_df.index.unique()) == len(jobs_df)
        assert jobs_df["ncpu"].sum() > 0


def test_get_jobs():
    jobs_df = bjobsusers.get_jobs("RUN", fake_bjobs)
    assert isinstance(jobs_df, pd.DataFrame)
    assert "ncpu" in jobs_df.columns
    assert "user" in jobs_df.index.name
    assert not jobs_df.empty
    assert len(jobs_df.index.unique()) == len(jobs_df)
    assert jobs_df["ncpu"].sum() > 0

    jobs_df = bjobsusers.get_jobs("RUN", bjobs_errors)
    assert isinstance(jobs_df, pd.DataFrame)
    assert jobs_df.empty


def test_userinfo():
    names = (
        "Foo Barrer (foo.bar.com)",
        "Føø Bårrær (foo.latin1.utf8.com)",
    )

    # assert isinstance(fake_finger(''), unicode)  # only relevant for Python 2
    for name in names:
        usersummary = bjobsusers.userinfo("foobar", FakeFinger(name))
        assert isinstance(usersummary, str)
        assert "Login" not in usersummary
        assert name in usersummary


def test_systemfinger():
    currentuser = os.getlogin()
    if not currentuser:
        return
    usersummary = bjobsusers.userinfo(currentuser, bjobsusers.call_finger)
    assert isinstance(usersummary, str)
    print("Myself is: " + usersummary)
    assert "Login" not in usersummary