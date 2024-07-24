from utils import *

# Specify a desired year
papers, n_pubmed, n_crossref = find_ibet_papers_for_specific_year(2012)
res = export_data_to_pdf(papers)
print("Number of papers in pubmed: ", n_pubmed)
print("Number of papers in crossref: ", n_crossref)