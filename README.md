# ArcOneSessionExtractor
The ArcOne session extractor is rather one big tool but a set of small tools or is planned to be in the future.

## STDP Extractor
The stdp extractor can be used to extract all stdp blocks from an ArcOne session and paste each into its own csv-file which then can be further processed by data analysation tools (e.g. Excel, ...). It is usefull when
a rather big session needs to be processed and should be used when results need to be put into a paper or thesis.

### Usage
It is a console based application with a small set of arguemtns and flags to set. The two most important arguments to pass are the source file path (-s <path>) and destination file path template (-d <path>). The -s command
specifies the ArcOne session ro process while the dest file template is used as a template for the output file/s. The tool will append a "_<stdp_block_index>" after the file name and before the file type extension (".csv").
Take a look at the following example:

     python stdp_extractor.py -s c:\stdp\session_a.csv -d c:\stdp\blocks\block.csv

With a stdp block count of 5 in session_a.csv this will result in the following files in folder "c:\stdp\blocks\":

     .\block_0.csv
     .\block_1.csv
     .\block_2.csv
     .\block_3.csv
     .\block_4.csv
