"""Exception classes for the :py:mod:~`eof2` package.""" 
# (c) Copyright 2010-2012 Andrew Dawson. All Rights Reserved. 
# 
# This file is part of eof2.
# 
# eof2 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# eof2 is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU General Public License
# along with eof2.  If not, see <http://www.gnu.org/licenses/>.


class EofError(Exception):
    """Generic exception class for errors in the eof2 package."""
    pass


class EofToolError(Exception):
    """Generic exception class for errors in the supplementary tools."""
    pass

