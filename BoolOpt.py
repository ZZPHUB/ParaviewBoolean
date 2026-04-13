#Fucking Vtk Boolean Operation Filter
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview.util.vtkAlgorithm import smproxy, smproperty, smhint, smdomain
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from vtkmodules.util.numpy_support import vtk_to_numpy,numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkDataObject,vtkCellArray
from vtkmodules.vtkCommonCore import vtkDoubleArray,vtkDataArraySelection,vtkDataArray,vtkPoints
import manifold3d
import numpy as np

MYDEBUG = True

@smproxy.filter(label="BoolOpt")
@smproperty.input(name="Input1", port_index=1)
@smdomain.datatype(dataTypes=["vtkDataSet"], composite_data_supported=False)
@smproperty.input(name="Input0", port_index=0)
@smdomain.datatype(dataTypes=["vtkDataSet"], composite_data_supported=False)
class ExampleTwoInputFilter(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=2, nOutputPorts=1, outputType="vtkPolyData")
        self._Operation = "Union"  

    @smproperty.intvector(name="Operation",default_values="0")
    @smdomain.xml("""
        <EnumerationDomain name="enum">
            <Entry value="0" text="Union"/>>
            <Entry value="1" text="Intersection"/>>
            <Entry value="2" text="Difference"/>>
        </EnumerationDomain>
    """"")
    def SetOperation(self, value):
        if value == 0:
            self._Operation = "Union"
        elif value == 1:
            self._Operation = "Intersection"
        elif value == 2:
            self._Operation = "Difference"
        else:
            self._Operation = "Union"
        self.Modified()  # 通知流水线数据已更新

    def FillInputPortInformation(self, port, info):
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet")
        else:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet")
        return 1
    
    def _PolyTriFilter(self,Data):
        GeoF = vtkGeometryFilter()
        GeoF.SetInputData(Data)
        GeoF.Update()

        TriF = vtkTriangleFilter()
        TriF.SetInputConnection(GeoF.GetOutputPort())
        TriF.Update()

        return TriF.GetOutput()
    
    def _Vtk2Manifold(self,Data):
        # 1. 提取顶点坐标
        points_vtk = Data.GetPoints().GetData()
        vertices = vtk_to_numpy(points_vtk)
        print("Vtk2Manifold Vertices:",vertices) if MYDEBUG else None

        # 2. 提取面片索引 (仅处理三角形)
        polys = Data.GetPolys()
        if polys is None:
            raise ValueError("VTK PolyData 中不包含多边形/三角形数据")

        polys_array = vtk_to_numpy(polys.GetData())
        faces = []
        i = 0
        while i < len(polys_array):
            num_verts = polys_array[i]
            if num_verts != 3:
                # 实际应用中，这里可以添加三角化逻辑，否则跳过或报错
                print(f"警告: 发现非三角形面片 (顶点数: {num_verts})，已跳过。PyMesh 主要处理三角形。")
                i += num_verts + 1
                continue
            faces.append(polys_array[i+1 : i+1+num_verts])
            i += num_verts + 1
    
        faces = np.array(faces, dtype=np.int32)
        print("Vtk2Manifold Faces:",faces) if MYDEBUG else None

        # 3. 创建 Manifold3D 对象
        mesh = manifold3d.Mesh(vertices, faces)
        mesh.merge()
        #print("Vtk2Manifold mesh:",mesh.vert_properties, mesh.tri_verts) if MYDEBUG else None
        MF = manifold3d.Manifold(mesh)

        if(MF.is_empty()):
            print("Vtk2Manifold: Empty Manifold")
            print("Vtk2Manifold Status:",MF.status())
            return None
        
        #if status != manifold3d.Error.NoError:
        #    print(f"Vtk2Manifold Status Error: {status}")


        #if MYDEBUG:
            #TmpMesh = MF.to_mesh()
            #print("Vtk2Manifold Vertices:",TmpMesh.vert_properties) if MYDEBUG else None
            #print("Vtk2Manifold Faces:",TmpMesh.tri_verts) if MYDEBUG else None
        return MF

    
    def _SelfBool(self,Data0,Data1):
        if(self._Operation == "Union"):
            return Data0 + Data1
        elif(self._Operation == "Intersection"):
            return Data0 ^ Data1
        elif(self._Operation == "Difference"):
            return Data0 - Data1
        else:
            return None
    
    def _Manifold2Vtk(self,Data):
        Mesh = Data.to_mesh()
        #print("Manifold2Vtk Vertices:",Mesh.vert_properties) if MYDEBUG else None
        #print("Manifold2Vtk Faces:",Mesh.tri_verts) if MYDEBUG else None
        Ptc = Mesh.vert_properties  # 顶点数组
        Faces = Mesh.tri_verts  # 三角形数组
        #print("Manifold2Vtk Vertices:",Ptc) if MYDEBUG else None
        #print("Manifold2Vtk Faces:",Faces) if MYDEBUG else None
        return Ptc,Faces

    def RequestData(self, Request, InputInfo, OutputInfo):  
        from vtkmodules.vtkCommonDataModel import vtkDataSet
        TmpInputDs0 = vtkDataSet.GetData(InputInfo[0], 0)
        TmpInputDs1 = vtkDataSet.GetData(InputInfo[1], 0)

        InputDs0 = self._PolyTriFilter(TmpInputDs0)
        InputDs1 = self._PolyTriFilter(TmpInputDs1)

        MF0 = self._Vtk2Manifold(InputDs0)
        MF1 = self._Vtk2Manifold(InputDs1)

        if MF0 is None or MF1 is None:
            return 0

        print("Source 0:",self._Manifold2Vtk(MF0)) if MYDEBUG else None
        print("Source 1:",self._Manifold2Vtk(MF1)) if MYDEBUG else None

        MF = self._SelfBool(MF0,MF1)

        print("Result:",self._Manifold2Vtk(MF)) if MYDEBUG else None

        Ptc,Faces = self._Manifold2Vtk(MF)
        print("Ptc:",Ptc) if MYDEBUG else None
        print("Faces:",Faces) if MYDEBUG else None

        VPtc = vtkPoints()
        VPtc.SetData(numpy_to_vtk(Ptc,deep=True))

        VCell = vtkCellArray()
        for Face in Faces:
            VCell.InsertNextCell(3,Face)
        
        OutputDs = self.GetOutputData(OutputInfo, 0)
        OutputDs.SetPoints(VPtc)
        OutputDs.SetPolys(VCell)

        return 1
