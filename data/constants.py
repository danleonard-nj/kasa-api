import enum


class FormatConstants:
    DefaultTimeFormat = '%Y-%m-%dT%H:%M:%S'


class MongoConstants:
    ConnectionStringName = 'connection_string'
    DatabaseName = 'Kasa'
    KasaDeviceCollectionName = 'KasaDevice'
    KasaLinkCollectionName = 'KasaLink'
    KasaPresetCollectionName = 'KasaPreset'
    KasaSceneCollectionName = 'KasaScene'
    KasaDeviceHistoryCollectionName = 'KasaDeviceHistory'
    KasaRegionCollectionName = 'KasaRegion'
    KasaSceneCategoryCollectionName = 'KasaSceneCategory'


class KasaActionType(enum.Enum):
    TogglePlug = 1
    SetLight = 2


class AuthScheme:
    WRITE = 'kasa-write'
    READ = 'kasa-read'
    EVENT = 'kasa-event'
    EXECUTE = 'kasa-execute'
