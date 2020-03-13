import io
import os
import arcpy

import pandas as pd


def table_to_data_frame(in_table, input_fields=None, where_clause=None, replace_false_vals=True):
    """
    Convert all or a subset of fields in an arcgis table into a pandas dataframe with an object ID index.
    The function accepts an optional where clause to filter rows and an optional flag to convert 
    false values (EXCEPT 0) to None.
    """
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    if replace_false_vals:
        # Need to introspect each row..
        data = []
        for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause):
            new_row = []
            for value in row:
                if isinstance(value, (str, unicode)):
                    new_row.append(value if value.strip() else None)
                else:
                    new_row.append(value)
            data.append(new_row)
    else:
        data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    return fc_dataframe


class Toolbox(object):
    def __init__(self):
        self.label = "Describe Feature Class Toolbox"
        self.alias = "Describe_Feature_Class_Toolbox"
        self.tools = [Describe_Table]


class Describe_Table(object):
    def __init__(self):
        self.label = "Describe Feature Class"
        self.description = "Describe_Feature_Class"
        self.canRunInBackground = True

    def getParameterInfo(self):
        inputTable=arcpy.Parameter(
            displayName='Input Feature Class or Table',
            name='Input_Table',
            datatype= ['DEFeatureClass', 'DETable'],
            parameterType='Required',
            direction='Input',
            )
        outputText=arcpy.Parameter(
            displayName='Output Text File',
            name= 'Output_File',
            datatype= 'DEFile',
            parameterType= 'Required',
            direction='Output',
            )
        return [inputTable, outputText]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        inputTable, outputText = parameters
        inputTypes = ('FeatureClass', 'ShapeFile', 'Table')
        if inputTable.value:
            try:
                assert arcpy.Describe(inputTable.valueAsText).dataType in inputTypes
            except:
                inputTable.setErrorMessage('Not a Feature Class, Shapefile, or Table')
        if outputText.value:
            _, ext = os.path.splitext(outputText.valueAsText)
            if ext and ext.lower() != '.txt':
                outputText.setErrorMessage('Not a text file [.txt]')
        return

    def execute(self, parameters, messages):
        inputTable, outputText = parameters

        outputText = outputText.valueAsText
        outputText = outputText + '.txt' if not outputText.lower().endswith('.txt') else outputText
        df = table_to_data_frame(inputTable.value)
        buffer = io.StringIO()
        df.info(buf=buffer, verbose=True, memory_usage='Deep')
        with open(outputText, 'wb') as f:  
            f.write(buffer.getvalue())
            f.write(df.describe(include='all').to_string())
            
        return
