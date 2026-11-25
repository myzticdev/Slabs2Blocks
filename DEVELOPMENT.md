# Building Slabs2Blocks

Run these commands with Python 3.11 or later.

```sh
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/build.py
```

The build writes 13 installable ZIPs, a SHA-256 manifest and an All-Versions bundle to `dist/`. GitHub Actions builds and tests each change. Updating `.github/release-version` on main or pushing a version tag publishes the matching changelog section and archives.

`src/slabs.json` groups slab-to-block pairs by the version that introduced their vanilla crafting recipe. Each group adds to the previous groups. Use the plain parent block when the forward recipe accepts several blocks. Compare the pairs to the three-block, six-slab crafting recipes in the official Java client JAR for each affected version. Check both horizontal and shapeless vanilla recipes for collisions.

`scripts/build.py` defines the version boundaries. The modern stable ZIP uses overlays for the result schema at format 41, the recipe directory at 48, string ingredients at 57, and later slab additions. The preview differentiates formats 125.0 and 125.1 so packed ice brick and snow brick slabs appear in their respective snapshots.

For v1.0.0, the installed recipe sets were checked against vanilla game data across 34 versions. On a vanilla Java 1.21.11 server, reloading the ZIP added 61 recipes. Powered crafters produced the expected block for all 61 pairs. A mixed oak/spruce pair remained in the crafter, and a vertical stone brick slab pair produced vanilla chiseled stone bricks.
