from framework.auth.azure import AzureAd
from framework.auth.configuration import AzureAdConfiguration
from framework.configuration import Configuration


class AdRole:
    READ = 'Kasa.Read'
    WRITE = 'Kasa.Write'
    EXECUTE = 'Kasa.Execute'


def contains_role(token, role):
    roles = token.get('roles')
    if roles is None or role not in roles:
        return False

    return True


def configure_azure_ad(container):
    configuration = container.resolve(Configuration)

    # Hook the Azure AD auth config into the service
    # configuration
    ad_auth: AzureAdConfiguration = configuration.ad_auth
    azure_ad = AzureAd(
        tenant=ad_auth.tenant_id,
        audiences=ad_auth.audiences,
        issuer=ad_auth.issuer)

    azure_ad.add_authorization_policy(
        name='read',
        func=lambda t: contains_role(
            token=t,
            role=AdRole.READ
        ))

    azure_ad.add_authorization_policy(
        name='write',
        func=lambda t: contains_role(
            token=t,
            role=AdRole.WRITE
        ))

    azure_ad.add_authorization_policy(
        name='default',
        func=lambda t: True)

    azure_ad.add_authorization_policy(
        name='execute',
        func=lambda t: contains_role(
            token=t,
            role=AdRole.EXECUTE
        ))

    return azure_ad
