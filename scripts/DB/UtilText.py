#!/usr/bin/env python
# coding: utf-8

# In[2]:


# TEXT FUNCTIONS
def compareLists(listA,listB):
    indicesA,indicesB=[i for i in range(len(listA))],[i for i in range(len(listB))]
    resultA,resultB=[],[]
    for ixB,valB in enumerate(listB):
        if ixB not in indicesB: # skip if indexA already taken 
            continue
        indicesB.remove(ixB)
        valueBinA = False
        indexInA = -1
        for ixA,valA in enumerate(listA): # find value of A in B
            if ixA not in indicesA: # skip if indexB already taken
                continue
            if valB==valA:
                valueBinA=True
                indexInA = ixA
                # find previous elements in B that match in A, valB must be unique
                tmpA=indicesA[:indicesA.index(listA.index(valA))]
                for ixSubA,valSubA in enumerate(tmpA):
                    valueAinB=False
                    for iB in range(ixB+1,len(listB)):
                        if listB[iB]==listA[valSubA]:
                            valueAinB=True
                            resultB.append(listB[iB])
                            resultA.append(listA[valSubA])
                            indicesB.remove(iB)
                            break
                    if not valueAinB:
                        resultB.append('')
                        resultA.append(listA[valSubA])
                    indicesA.remove(valSubA)
        resultB.append(listB[ixB])
        if valueBinA:
            # Add element in B to results and remove used index in B
            resultA.append(listA[indexInA])
            indicesA.remove(indexInA)
        else:
            resultA.append('')
    while len(indicesA)>0:
        resultB.append('')
        resultA.append(listA[indicesA.pop(0)])
    return resultA,resultB
def isValueNumeric(value):
    isNumeric=True
    try:
        float(value)
    except:
        isNumeric=False
    return isNumeric
def ignoreValue2Compare(value,withNumbers=False):
    ignoreValue = value is None or str(value).strip() in ['','-','_','Yes','No']
    #COMMENT LINE TO CONSIDER NUMERIC VALUES
    ignoreValue = ignoreValue or isValueNumeric(value)
    if ignoreValue:
        return True
    elif not withNumbers and isValueNumeric(value):
        return True
    return False        
def letter2index(letters):
    letters=letters.upper()
    i=0
    total=0
    for letter in reversed(letters):
        if i>0:
            total+=26**i*(ord(letter)-65+1)
        else:
            total+=26**i*(ord(letter)-65)
        i+=1
    return total
def index2letter(value):
    letters=chr(value%26+65)
    value=value//26
    while value>0:
        if value%26==0:
            tmp='Z'
            value=value//26-1
        else:
            tmp=chr(value%26+65-1)
            value=value//26
        letters = tmp+letters
    return letters


# In[1]:


# PANDAS DATAFRAME FUNCTIONS
import pandas as pd
def checkMissingValues(df1,df2,withNumbers=False):
    hasChanged = False
    dict1,diff_dict={},{1:{},2:{}}
    for ix,row in df1.iterrows():
        for col,value in row.items():
            if ignoreValue2Compare(value,withNumbers):
                continue
            if value not in dict1:
                dict1[value]=[col+' '+str(ix)]
            else:
                dict1[value].append(col+' '+str(ix))
    df1_out,df2_out = df1.copy(),df2.copy()
    for col in df1_out:
        df1_out[col]=df1_out[col].astype(str)
    for col in df2_out:
        df2_out[col]=df2_out[col].astype(str)
    for ix,row in df2.iterrows():
        for col,value in row.items():
            if ignoreValue2Compare(value,withNumbers):
                continue
            if value not in dict1:
                df2_out.at[ix,col]=value
                diff_dict[2][col+str(ix)] = value
                hasChanged=True
            else:
                cell1=dict1[value].pop(0)
                arr_cell1=cell1.split()
                col1,ix1=arr_cell1[0],int(arr_cell1[1])
                if len(dict1[value])==0:
                    del dict1[value]
                df1_out.at[ix1,col1]=col+' '+str(ix)
                df2_out.at[ix,col]=cell1
    for value in dict1:
        for cell in dict1[value]:
            arr_cell = cell.split()
            col,ix = arr_cell[0],arr_cell[1]
            diff_dict[1][col+str(ix)] = value
            hasChanged=True
    return df1_out,df2_out,diff_dict,hasChanged
def compareDfs(df1,df2,withNumbers=False):
    numRows_l1,numCols_l1 = len(df1.index),len(df1.columns)
    numRows_l2,numCols_l2 = len(df2.index),len(df2.columns)
    if numRows_l1 != numRows_l2:
        print('Total rows:',numRows_l1,'!=',numRows_l2)
    if numCols_l1 != numCols_l2:
        print('Total columns:',numCols_l1,'!=',numCols_l2)
    return checkMissingValues(df1,df2,withNumbers)
def findValueInDf(df,value): # return first occurrence
    for ix,row in df.iterrows():
        for col,valueDf in row.items():
            if isinstance(valueDf, str):
                valueDf = str(valueDf).strip()
            if value == valueDf:
                return ix,col
    raise LookupError("Value '{}' was not found".format(value))
def findValueAllInDf(df,value): # return all occurrence
    positions = []
    doesValueExist = False
    for ix,row in df.iterrows():
        for col,valueDf in row.items():
            if isinstance(valueDf, str):
                valueDf = str(valueDf).strip()
            if value == valueDf:
                doesValueExist = True
                positions.append((ix,col))
    if doesValueExist:
        return positions
    else:
        raise LookupError("Value '{}' was not found".format(value))





# %%
