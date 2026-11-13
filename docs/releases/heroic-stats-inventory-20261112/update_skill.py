"""Compatibility entrypoint for the observed published-release knowledge update."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from update_inventory_knowledge import main


if __name__=='__main__':main()
