// Install in Assets/NightcapWingedHelmet/Editor with the decoded fit FBX and BMPs.
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

[InitializeOnLoad]
public static class WingedHelmetFitPreview
{
    const string Root = "Assets/NightcapWingedHelmet/SnugFits20261004";
    static WingedHelmetFitPreview() { EditorApplication.delayCall += Build; }
    [MenuItem("Nightcap/Inspect Snug Classic Helmet Fits")]
    public static void Build()
    {
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        { EditorApplication.delayCall += Build; return; }
        if (File.Exists(Root + "/verified.json")) { RefreshCapture(); return; }
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "/classic-24-snug-fits.fbx");
        if (!asset) return;
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        if (!shader) throw new System.Exception("URP Lit shader unavailable");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
        SceneManager.SetActiveScene(scene);
        var fits = (GameObject)PrefabUtility.InstantiatePrefab(asset, scene);
        var textures = Directory.GetFiles(Root, "*.bmp");
        var materials = new System.Collections.Generic.Dictionary<string, Material>();
        var renderers = fits.GetComponentsInChildren<MeshRenderer>();
        foreach (var renderer in renderers)
        {
            renderer.sharedMaterials = renderer.sharedMaterials.Select(source => {
                if (materials.TryGetValue(source.name, out var found)) return found;
                var path = textures.Single(p => source.name.Contains(Path.GetFileNameWithoutExtension(p)));
                var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path.Replace('\\','/'));
                if (!texture) throw new System.Exception("Missing native texture: " + path);
                var mat = new Material(shader) { name = source.name };
                mat.SetTexture("_BaseMap", texture); mat.SetColor("_BaseColor", Color.white);
                mat.SetFloat("_Smoothness", .25f);
                AssetDatabase.CreateAsset(mat, Root + "/" + source.name + ".mat");
                materials[source.name] = mat;
                return mat;
            }).ToArray();
        }
        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
        var camera = new GameObject("Snug Fit Camera").AddComponent<Camera>();
        camera.transform.position = bounds.center + Vector3.forward * 15;
        camera.transform.LookAt(bounds.center); camera.orthographic = true;
        camera.orthographicSize = Mathf.Max(bounds.size.y * .55f, bounds.size.x / 3f * 1.1f);
        camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.06f,.08f,.1f);
        var light = new GameObject("Fit Studio Key").AddComponent<Light>();
        light.type = LightType.Directional; light.intensity = 1.5f;
        light.transform.rotation = Quaternion.Euler(25,160,0);
        RenderSettings.ambientLight = new Color(.4f,.4f,.4f);
        EditorSceneManager.SaveScene(scene, Root + "/SnugClassicFits.unity");
        Selection.activeGameObject = fits;
        if (SceneView.lastActiveSceneView)
            SceneView.lastActiveSceneView.LookAt(bounds.center, camera.transform.rotation, bounds.size.magnitude * .6f);
        AssetDatabase.SaveAssets();
        RefreshCapture();
        File.WriteAllText(Root + "/verified.json", JsonUtility.ToJson(new Evidence {
            status = "Decoded native fits imported and rendered in Unity; native wearer QA pending",
            heads = renderers.Length, materials = materials.Count, unity = Application.unityVersion
        }, true));
    }
    [MenuItem("Nightcap/Refresh Snug Fit Capture")]
    public static void RefreshCapture()
    {
        var scene = SceneManager.GetSceneByPath(Root + "/SnugClassicFits.unity");
        if (!scene.isLoaded)
            scene = EditorSceneManager.OpenScene(Root + "/SnugClassicFits.unity", OpenSceneMode.Additive);
        var roots = scene.GetRootGameObjects();
        var camera = roots.SelectMany(o => o.GetComponentsInChildren<Camera>()).Single();
        // Other user scenes stay loaded but must not overlap the inspection.
        foreach (var renderer in roots.SelectMany(o => o.GetComponentsInChildren<Renderer>()))
            renderer.gameObject.layer = 30;
        camera.cullingMask = 1 << 30;
        EditorSceneManager.SaveScene(scene);
        var target = new RenderTexture(2100,1400,24);
        camera.targetTexture = target; camera.Render();
        var previous = RenderTexture.active; RenderTexture.active = target;
        var image = new Texture2D(2100,1400,TextureFormat.RGB24,false);
        image.ReadPixels(new Rect(0,0,2100,1400),0,0); image.Apply();
        File.WriteAllBytes(Root + "/unity-snug-fits.png", image.EncodeToPNG());
        RenderTexture.active = previous; camera.targetTexture = null;
        Object.DestroyImmediate(image); Object.DestroyImmediate(target);
    }
    [System.Serializable] class Evidence { public string status; public int heads, materials; public string unity; }
}
