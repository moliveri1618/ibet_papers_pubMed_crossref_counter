from utils import *

# Specify a desired year
papers = find_ibet_papers_for_specific_year(2012)
res = export_data_to_pdf(papers)
