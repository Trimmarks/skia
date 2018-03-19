# Patch base for VersaType

`trimmarks-patch-base` is the main branch.

次のように作成した。

```
git add remote murkaami-san git@github.com:MurakamiShinyu/skia.git
git log --no-merge --author='MurakamiShinyu' | grep ^commit | sed -i 's/commit //' > patch-commits
tail -r patch-commits | xargs git cherry-pick
```

必要に応じて、このbranchを更新していく。

`skia-patch.diff`をCEFのカスタムビルド時に利用する。
