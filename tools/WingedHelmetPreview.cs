// Copy to Assets/NightcapWingedHelmet/Editor in the user's Unity project.
// Builds a separate inspection scene once after the exported FBX is imported.
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

[InitializeOnLoad]
public static class WingedHelmetPreview
{
    const string Root = "Assets/NightcapWingedHelmet";
    static WingedHelmetPreview() { EditorApplication.delayCall += Build; }
    [MenuItem("Nightcap/Inspect Winged Paladin Helmet")]
    public static void Build()
    {
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        { EditorApplication.delayCall += Build; return; }
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "/winged-paladin-helmet.fbx");
        if (!asset) return;
        if (File.Exists(Root + "/preview-built.json")) { Refresh(); return; }
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
        SceneManager.SetActiveScene(scene);
        var helmet = (GameObject)PrefabUtility.InstantiatePrefab(asset, scene);
        helmet.name = "Winged Paladin Helmet - inspection";
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        if (!shader) throw new System.Exception("URP Lit shader is unavailable");
        var mats = new System.Collections.Generic.Dictionary<string, Material>();
        foreach (var renderer in helmet.GetComponentsInChildren<MeshRenderer>())
        {
            var source = renderer.sharedMaterials;
            for (int i = 0; i < source.Length; ++i)
            {
                var name = source[i] ? source[i].name : "Silver";
                if (!mats.TryGetValue(name, out var mat))
                {
                    mat = new Material(shader) { name = name };
                    bool gold = name.Contains("Gold"), wing = name.Contains("Wing");
                    mat.SetColor("_BaseColor", gold ? new Color(.62f,.39f,.07f) : wing ? new Color(.87f,.88f,.82f) : new Color(.58f,.64f,.70f));
                    mat.SetFloat("_Metallic", wing ? .27f : .72f);
                    mat.SetFloat("_Smoothness", wing ? .51f : .64f);
                    AssetDatabase.CreateAsset(mat, Root + "/" + name.Replace(" ", "_") + ".mat");
                    mats[name] = mat;
                }
                source[i] = mat;
            }
            renderer.sharedMaterials = source;
        }
        var camera = new GameObject("Helmet Inspection Camera").AddComponent<Camera>();
        camera.transform.position = new Vector3(1.65f,1.3f,2.9f);
        camera.transform.LookAt(new Vector3(0,.52f,0));
        camera.orthographic = true; camera.orthographicSize = .675f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.035f,.047f,.065f);
        var light = new GameObject("Studio Key").AddComponent<Light>();
        light.type = LightType.Directional; light.intensity = 1.5f;
        light.transform.rotation = Quaternion.Euler(35,-35,0);
        RenderSettings.ambientLight = new Color(.35f,.38f,.42f);
        var bounds = new Bounds(); bool first = true; int triangles = 0;
        foreach (var renderer in helmet.GetComponentsInChildren<Renderer>())
        { if (first) { bounds = renderer.bounds; first = false; } else bounds.Encapsulate(renderer.bounds); }
        foreach (var filter in helmet.GetComponentsInChildren<MeshFilter>())
            triangles += (int)filter.sharedMesh.GetIndexCount(0) / 3;
        EditorSceneManager.SaveScene(scene, Root + "/WingedPaladinInspection.unity");
        Selection.activeGameObject = helmet;
        if (SceneView.lastActiveSceneView)
            SceneView.lastActiveSceneView.LookAt(bounds.center, Quaternion.Euler(8,145,0), bounds.size.magnitude * .8f);
        File.WriteAllText(Root + "/preview-built.json", JsonUtility.ToJson(new Evidence {
            status = "Unity imported preview; in-game verification pending",
            triangles = triangles, bounds = bounds.size, unity = Application.unityVersion
        }, true));
        AssetDatabase.SaveAssets();
        Refresh();
        Debug.Log("Nightcap winged helmet imported, separate inspection scene saved. Triangles: " + triangles);
    }
    [MenuItem("Nightcap/Refresh Helmet Metal Preview")]
    public static void Refresh()
    {
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/humch0301.bmp");
        if (texture)
            foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { Root }))
            {
                var mat = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                mat.SetTexture("_BaseMap", texture);
                mat.SetColor("_BaseColor", Color.white);
                EditorUtility.SetDirty(mat);
            }
        var camera = GameObject.Find("Helmet Inspection Camera");
        if (camera)
        {
            var helmet = GameObject.Find("Winged Paladin Helmet - inspection");
            Vector3 nasal = Vector3.zero, dome = Vector3.zero;
            foreach (var renderer in helmet.GetComponentsInChildren<MeshRenderer>())
            {
                if (renderer.name.StartsWith("07 ")) nasal = renderer.bounds.center;
                if (renderer.name.StartsWith("01 ")) dome = renderer.bounds.center;
            }
            var front = nasal - dome; front.y = 0; front.Normalize();
            var side = Vector3.Cross(Vector3.up,front);
            camera.transform.position = front*2.9f + side*1.2f + Vector3.up*1.1f;
            camera.transform.LookAt(new Vector3(0,.52f,0));
            EditorSceneManager.MarkSceneDirty(camera.scene);
            EditorSceneManager.SaveScene(camera.scene);
            File.WriteAllText(Root+"/preview-refreshed.json", "{\"nasal\":\""+nasal+"\",\"dome\":\""+dome+"\",\"camera\":\""+camera.transform.position+"\"}");
        }
        AssetDatabase.SaveAssets();
    }
    [System.Serializable] class Evidence { public string status; public int triangles; public Vector3 bounds; public string unity; }
}
