from pyramid.view import view_config
from ..Models import (
    DBSession,
    Station,
    StationType,
    Observation,
    FieldActivity_ProtocoleType
    )
from ecoreleve_server.GenericObjets.FrontModules import (FrontModule,ModuleField)
from ecoreleve_server.GenericObjets import ListObjectWithDynProp
import transaction
import json
from datetime import datetime
import datetime as dt
import pandas as pd
import numpy as np
from sqlalchemy import select, and_,cast, DATE,func
from sqlalchemy.orm import aliased
from pyramid.security import NO_PERMISSION_REQUIRED




prefix = 'stations'


# @view_config(route_name= prefix, renderer='json', request_method = 'PUT')
# def updateListStations(request):
#     # TODO 
#     # update a list of stations 
#     return

# @view_config(route_name= prefix, renderer='json', request_method = 'GET')
# def getListStations(request):
#     # TODO 
#     # return list of stations 
#     # can search/filter
#     return

@view_config(route_name= prefix+'/action', renderer='json', request_method = 'GET', permission = NO_PERMISSION_REQUIRED)
def actionOnStations(request):
    print ('\n*********************** Action **********************\n')
    dictActionFunc = {
    'count' : count,
    'forms' : getForms,
    '0' : getForms,
    'fields': getFields
    }
    actionName = request.matchdict['action']
    return dictActionFunc[actionName](request)

def count (request) :
#   ## TODO count stations
    print('*****************  STATION COUNT***********************')
    #nb = DBSession.query(func.count(Station.ID))
    nb = DBSession.query(Station).count()
    print(nb)
    return nb

def getForms(request) :

    typeSta = request.params['ObjectType']
    print('***************** GET FORMS ***********************')
    ModuleName = 'StaForm'
    Conf = DBSession.query(FrontModule).filter(FrontModule.Name==ModuleName ).first()
    newSta = Station(FK_StationType = typeSta)
    newSta.init_on_load()
    schema = newSta.GetDTOWithSchema(Conf,'edit')
    del schema['schema']['creationDate']
    return schema

def getFields(request) :
#     ## TODO return fields Station
    return

@view_config(route_name= prefix+'/id', renderer='json', request_method = 'GET',permission = NO_PERMISSION_REQUIRED)
def getStation(request):

    print('***************** GET STATION ***********************')
    id = request.matchdict['id']
    curSta = DBSession.query(Station).get(id)
    curSta.LoadNowValues()

    # if Form value exists in request --> return data with schema else return only data
    if 'FormName' in request.params :
        ModuleName = request.params['FormName']
        try :
            DisplayMode = request.params['DisplayMode']
        except : 
            DisplayMode = 'display'

        Conf = DBSession.query(FrontModule).filter(FrontModule.Name=='StaForm' ).first()
        response = curSta.GetDTOWithSchema(Conf,DisplayMode)
    else : 
        response  = curSta.GetFlatObject()

    return response


@view_config(route_name= prefix+'/id', renderer='json', request_method = 'DELETE',permission = NO_PERMISSION_REQUIRED)
def deleteStation(request):
    id_ = request.matchdict['id']
    curSta = DBSession.query(Station).get(id_)
    DBSession.delete(curSta)
    transaction.commit()

    return True

@view_config(route_name= prefix+'/id', renderer='json', request_method = 'PUT')
def updateStation(request):

    print('*********************** UPDATE Station *****************')
    data = request.json_body
    id = request.matchdict['id']
    curSta = DBSession.query(Station).get(id)
    curSta.LoadNowValues()
    curSta.UpdateFromJson(data)
    transaction.commit()
    return {}

@view_config(route_name= prefix, renderer='json', request_method = 'POST')
def insertStation(request):

    data = request.POST.mixed()
    if 'data' not in data :
        print('_______INsert ROW *******')
        return insertOneNewStation(request)
    else :
        print (data['data'])
        print('_______INsert LIST')

        return insertListNewStations(request)

def insertOneNewStation (request) :

    data = {}
    for items , value in request.json_body.items() :
        if value != "" :
            data[items] = value
    print('------------------------------')
    print (data)
    newSta = Station(FK_StationType = data['FK_StationType'], creator = request.authenticated_userid)
    newSta.StationType = DBSession.query(StationType).filter(StationType.ID==data['FK_StationType']).first()
    newSta.init_on_load()
    newSta.UpdateFromJson(data)
    DBSession.add(newSta)
    DBSession.flush()
    return {'id': newSta.ID}

def insertListNewStations(request):
    data = request.POST.mixed()
    data = data['data']
    DTO = json.loads(data)
    data_to_insert = []
    format_dt = '%Y-%m-%d %H:%M:%S'
    format_dtBis = '%Y-%d-%m %H:%M:%S'
    dateNow = datetime.now()

    ##### Rename field and convert date #####
    for row in DTO :
        newRow = {}
        newRow['LAT'] = row['latitude']
        newRow['LON'] = row['longitude']
        newRow['Name'] = row['name']
        newRow['fieldActivityId'] = 1
        newRow['precision'] = row['Precision']
        newRow['creationDate'] = dateNow
        newRow['creator'] = request.authenticated_userid
        newRow['FK_StationType']=4
        newRow['id'] = row['id']

        try :
            newRow['StationDate'] = datetime.strptime(row['waypointTime'],format_dt)
        except :
            newRow['StationDate'] = datetime.strptime(row['waypointTime'],format_dtBis)
        data_to_insert.append(newRow)

    ##### Load date into pandas DataFrame then round LAT,LON into decimal(5) #####
    DF_to_check = pd.DataFrame(data_to_insert)
    DF_to_check['LAT'] = np.round(DF_to_check['LAT'],decimals = 5)
    DF_to_check['LON'] = np.round(DF_to_check['LON'],decimals = 5)
    
    ##### Get min/max Value to query potential duplicated stations #####
    maxDate = DF_to_check['StationDate'].max(axis=1)
    minDate = DF_to_check['StationDate'].min(axis=1)
    maxLon = DF_to_check['LON'].max(axis=1)
    minLon = DF_to_check['LON'].min(axis=1)
    maxLat = DF_to_check['LAT'].max(axis=1)
    minLat = DF_to_check['LAT'].min(axis=1)

    ##### Retrieve potential duplicated stations from Database #####
    query = select([Station]).where(
        and_(
            Station.StationDate.between(minDate,maxDate),
            Station.LAT.between(minLat,maxLat)
            ))
    result_to_check = DBSession.execute(query).fetchall()

    if result_to_check :
        ##### IF potential duplicated stations, load them into pandas DataFrame then join data to insert on LAT,LON,DATE #####
        result_to_check = pd.DataFrame(data=result_to_check, columns = Station.__table__.columns.keys())
        result_to_check['LAT'] = result_to_check['LAT'].astype(float)
        result_to_check['LON'] = result_to_check['LON'].astype(float)

        merge_check = pd.merge(DF_to_check,result_to_check , on =['LAT','LON','StationDate'])

        ##### Get only non existing data to insert #####
        DF_to_check = DF_to_check[~DF_to_check['id'].isin(merge_check['id'])]

    DF_to_check = DF_to_check.drop(['id'],1)
    data_to_insert = json.loads(DF_to_check.to_json(orient='records',date_format='iso'))

    ##### Build block insert statement and returning ID of new created stations #####
    if len(data_to_insert) != 0 :
        stmt = Station.__table__.insert(returning=[Station.ID]).values(data_to_insert)
        res = DBSession.execute(stmt).fetchall()
        result = list(map(lambda y: y[0], res))
    else : 
        result = []

    response = {'exist': len(DTO)-len(data_to_insert), 'new': len(data_to_insert)}
    
    return response 

@view_config(route_name= prefix, renderer='json', request_method = 'GET', permission = NO_PERMISSION_REQUIRED)
def searchStation(request):

    data = request.params
    searchInfo = {}
    searchInfo['criteria'] = []
    if 'criteria' in data : 
        searchInfo['criteria'].extend(data['criteria'])

    elif 'lastImported' in data :
        o = aliased(Station)
        
        criteria = [
        {'Column' : 'creator',
        'Operator' : '=',
        'Value' : request.authenticated_userid
        },
        {'Query':'Observation',
        'Column': 'None',
        'Operator' : 'not exists',
        'Value': select([Observation]).where(Observation.FK_Station == Station.ID)
        },
        {'Query':'Station',
        'Column': 'None',
        'Operator' : 'not exists',
        'Value': select([o]).where(cast(o.creationDate,DATE) > cast(Station.creationDate,DATE)) 
        },
        {'Column' : 'FK_StationType',
        'Operator' : '=',
        'Value' : 4
        },
        ]

        searchInfo['criteria'].extend(criteria)
    print(searchInfo['criteria'])
    listObj = ListObjectWithDynProp(DBSession,Station,searchInfo)
    response = listObj.GetFlatList()
    return response

@view_config(route_name= prefix+'/id/protocols', renderer='json', request_method = 'GET', permission = NO_PERMISSION_REQUIRED)
def GetProtocolsofStation (request) :

    sta_id = request.matchdict['id']
    data = {}
    searchInfo = {}
    criteria = [{'Column': 'FK_Station', 'Operator':'=','Value':sta_id}]

    response = []
    curSta = DBSession.query(Station).get(sta_id)
    try : 
        if 'criteria' in request.params or request.params == {} :
            print (' ********************** criteria params ==> Search ****************** ')

            searchInfo = data
            searchInfo['criteria'] = []
            searchInfo['criteria'].extend(criteria)
            listObs = ListObjectWithDynProp(DBSession,Observation,searchInfo)
            response = listObs.GetFlatList()
    except : 
        pass

    try :
        if 'FormName' in request.params : 
            print (' ********************** Forms in params ==> DATA + FORMS ****************** ')
            print(request.params)
            ModuleName = request.params['FormName']

            listObs = list(DBSession.query(Observation).filter(Observation.FK_Station == sta_id))
            listType =list(DBSession.query(FieldActivity_ProtocoleType
                ).filter(FieldActivity_ProtocoleType.FK_fieldActivity == curSta.fieldActivityId))
            Conf = DBSession.query(FrontModule).filter(FrontModule.Name == ModuleName ).first()

            ### TODO : if protocols exists, append the new protocol form at the after : 2 loops, no choice



            if listObs or listType:
                # max_iter = max(len(listObs),len(listType))
                listProto = {}

                for i in range(len(listObs)) :

                    try : 
                        DisplayMode = 'display'
                        obs = listObs[i]
                        typeName = obs.GetType().Name
                        typeID = obs.GetType().ID
                        obs.LoadNowValues()
                        try :
                            listProto[typeID]['obs'].append(obs.GetDTOWithSchema(Conf,DisplayMode))
                        except :
                            

                            listObsWithSchema = []
                            listObsWithSchema.append(obs.GetDTOWithSchema(Conf,DisplayMode))
                            listProto[typeID] = {'Name': typeName,'obs':listObsWithSchema}
                            pass
                    except : 
                      
                        pass

                for i in range(len(listType)) :
                    try : 
                        DisplayMode = 'edit'
                       
                        virginTypeID = listType[i].FK_ProtocoleType
                        virginObs = Observation(FK_ProtocoleType = virginTypeID)
                        viginTypeName = virginObs.GetType().Name
                        try :
                            if virginTypeID not in listProto :
                                virginForm = virginObs.GetDTOWithSchema(Conf,DisplayMode)
                                virginForm['data']['FK_ProtocoleType'] = virginTypeID
                                listProto[virginTypeID]['obs'].append(virginForm)
                        except :

                            if virginTypeID not in listProto :
                                listSchema = []
                                virginForm = virginObs.GetDTOWithSchema(Conf,DisplayMode)
                                virginForm['data']['FK_ProtocoleType'] = virginTypeID
                                listSchema.append(virginForm)
                                listProto[virginTypeID] = {'Name': viginTypeName,'obs':listSchema}
                                pass

                    except :
                        
                        pass

            globalListProto = [{'ID':objID, 'Name':listProto[objID]['Name'],'obs':listProto[objID]['obs'] } for objID in listProto.keys()]

            response = globalListProto
    except Exception as e :
        print (e)
        pass
    return response

@view_config(route_name= prefix+'/id/protocols', renderer='json', request_method = 'POST')
def insertNewProtocol (request) :

    data = {}
    for items , value in request.json_body.items() :
        if value != "" :
            data[items] = value
    data['FK_Station'] = request.matchdict['id']

    newProto = Observation(FK_ProtocoleType = data['FK_ProtocoleType'])
    newProto.ProtocoleType = DBSession.query(ProtocoleType).filter(ProtocoleType.ID==data['FK_ProtocoleType']).first()
    newProto.init_on_load()
    newProto.UpdateFromJson(data)
    DBSession.add(newProto)
    DBSession.flush()
    return {'id': newProto.ID}

@view_config(route_name= prefix+'/id/protocols/obs_id', renderer='json', request_method = 'PUT')
def updateObservation(request):

    print('*********************** UPDATE Observation *****************')
    data = request.json_body
    id_obs = request.matchdict['obs_id']
    curObs = DBSession.query(Observation).get(id_obs)
    curObs.LoadNowValues()
    curObs.UpdateFromJson(data)
    transaction.commit()
    return {}

@view_config(route_name= prefix+'/id/protocols/obs_id', renderer='json', request_method = 'DELETE')
def deleteObservation(request):

    print('*********************** DELETE Observation *****************')

    id_obs = request.matchdict['obs_id']
    curObs = DBSession.query(Observation).get(id_obs)
    DBSession.delete(curObs)
    transaction.commit()
    return {}

@view_config(route_name= prefix+'/id/protocols/obs_id', renderer='json', request_method = 'GET', permission = NO_PERMISSION_REQUIRED)
def getObservation(request):

    print('*********************** GET Observation *****************')
    
    id_obs = request.matchdict['obs_id']
    id_sta = request.matchdict['id']
    
    try :
        curObs = DBSession.query(Observation).filter(and_(Observation.ID ==id_obs, Observation.FK_Station == id_sta )).one()
        curObs.LoadNowValues()
        # if Form value exists in request --> return data with schema else return only data
        if 'FormName' in request.params :
            ModuleName = request.params['FormName']
            try :
                DisplayMode = request.params['DisplayMode']
            except : 
                DisplayMode = 'display'

            Conf = DBSession.query(FrontModule).filter(FrontModule.Name=='ObsForm' ).first()
            response = curObs.GetDTOWithSchema(Conf,DisplayMode)
        else : 
            response  = curObs.GetFlatObject()

    except Exception as e :
        print(e)
        response = {}

    return response

@view_config(route_name= prefix+'/id/protocols/action', renderer='json', request_method = 'GET', permission = NO_PERMISSION_REQUIRED)
def actionOnObs(request):
    print ('\n*********************** Action **********************\n')
    dictActionFunc = {
    'count' : countObs,
    'forms' : getObsForms,
    '0' : getObsForms,
    'fields': getObsFields
    }
    actionName = request.matchdict['action']
    return dictActionFunc[actionName](request)

def countObs (request) :
#   ## TODO count stations
    return

def getObsForms(request) :

    typeObs = request.params['ObjectType']
    print('***************** GET FORMS ***********************')
    ModuleName = 'ObsForm'
    Conf = DBSession.query(FrontModule).filter(FrontModule.Name==ModuleName ).first()
    newObs = Observation(FK_ProtocoleType = typeObs)
    newObs.init_on_load()
    schema = newObs.GetDTOWithSchema(Conf,'edit')
    del schema['schema']['creationDate']
    return schema

def getObsFields(request) :
#     ## TODO return fields Station
    return


