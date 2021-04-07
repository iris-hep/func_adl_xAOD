import FWCore.ParameterSet.Config as cms  # type: ignore

process = cms.Process("Demo")

process.load("FWCore.MessageService.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))

fileNamesArray = []
with open('/scripts/filelist.txt', 'r') as flist:
    for line in flist.readlines():
        fileNamesArray.append("file:" + line)

fileNamesTuple = tuple(fileNamesArray)
process.source = cms.Source("PoolSource",
                            # replace 'myfile.root' with the source file you want to use
                            fileNames=cms.untracked.vstring(
                                *fileNamesTuple
                            )
                            )

process.demo = cms.EDAnalyzer('Analyzer'
                              )

process.TFileService = cms.Service("TFileService",
                                   fileName=cms.string('/results/ANALYSIS.root')
                                   )

process.p = cms.Path(process.demo)
