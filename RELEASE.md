## Release
To the changes of the exporter take effect in [hardware-observer-operator](https://github.com/canonical/hardware-observer-operator) do the following steps:

1. Increase the tag version number. E.g: `git tag v<NEW_VERSION>` and push it `git push origin v<NEW_VERSION>`
2. Create a new release choosing the new tag and add the pertinent comment about the changes.
3. Change the requirements of [hardware-observer-operator](https://github.com/canonical/hardware-observer-operator/blob/main/requirements.txt#L7) to use the new tag
```
# requirements.txt
git+https://github.com/canonical/prometheus-hardware-exporter.git@v<NEW_VERSION>#egg=prometheus-hardware-exporter
```
