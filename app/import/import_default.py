# === Cấu hình ban đầu ===
import warnings
from dotenv import load_dotenv

# === Thư viện chuẩn của Python ===
import os
import sys
import copy
import time
import random
from datetime import timedelta, datetime
from typing import cast

# === Phân tích Dữ liệu (Data Analysis) ===
import pandas as pd
import numpy as np
import pandas_ta as ta

# === Tiện ích khác (Utilities) ===
import openpyxl
import dateutil
import os
import requests
import zipfile
import io

# Bỏ qua các cảnh báo không quan trọng để giữ cho output sạch sẽ
warnings.filterwarnings("ignore")
warnings.simplefilter('ignore', category=FutureWarning)

# Tắt cảnh báo ChainedAssignmentWarning của Pandas
pd.options.mode.chained_assignment = None

from import_env import load_env
