

class DTSmeMeta:
    """
     Mapped classes:
    
      - n = NftData
    
      - s = SecondaryMarketEvent
    
    
    """
    NAME = 'sme'  # Table Name
    
    PK = 'w'  # s.w
    
    SK = 'btt'  # s.btt
    
    GSI_SME_SME_ID = 'sme_gsi_sme_id'  # 
    
    GSI_SME_SME_ID_PK = 'sme_id'  # e.sme_id
    
    GSI_SME_NFT_EVENTS = 'sme_gsi_nft_events'  # 
    
    GSI_SME_NFT_EVENTS_PK = 'nft_id'  # n.nft_id
    
    GSI_SME_NFT_EVENTS_SK = 'timestamp'  # e.timestamp
    
    GSI_SME_COLLECTION_EVENTS = 'sme_gsi_collection_events'  # 
    
    GSI_SME_COLLECTION_EVENTS_PK = 'collection_id'  # n.collection_id
    
    GSI_SME_COLLECTION_EVENTS_SK = 'timestamp'  # e.timestamp
    
    LSI_SME_COLLECTION_NAME = 'sme_lsi_collection_name'  # 
    
    LSI_SME_COLLECTION_NAME_SK = 'collection_name'  # n.collection_name
    
    LSI_SME_TIMESTAMP = 'sme_lsi_timestamp'  # 
    
    LSI_SME_TIMESTAMP_SK = 'timestamp'  # e.timestamp
    
    LSI_SME_ET = 'sme_lsi_et'  # 
    
    LSI_SME_ET_SK = 'et'  # e.et
    

class DTNftMeta:
    """
     Mapped classes:
    
      - n = NftData
    
    
    """
    NAME = 'nft'  # Table Name
    
    PK = 'pk'  # ["n.nft_id","qfi#[a-z0-9_]"]
    
    SK = 'sk'  # ["n","co","n.collection_name.lower()"]
    
    GSI_NFT_COLLECTION_NFTS = 'nft_gsi_collection_nfts'  # 
    
    GSI_NFT_COLLECTION_NFTS_PK = 'collection_id'  # n.collection_id
    
    GSI_NFT_COLLECTION_NFTS_SK = 'nft_id'  # n.nft_id
    

class DTUserMeta:
    """
     Mapped classes:
    
      - u = User
    
    
    """
    NAME = 'user'  # Table Name
    
    PK = 'pk'  # u.user_id
    
    SK = 'sk'  # ["bn#<n.nft_id>","bc#<n.collection_id>"]
    
    GSI_USER_EMAILS = 'user_gsi_emails'  # 
    
    GSI_USER_EMAILS_PK = 'email'  # u.email
    
    GSI_USER_EMAILS_SK = 'sk'  # ["bn#<n.nft_id>","bc#<n.collection_id>"]
    
    GSI_USER_NICKNAME = 'user_gsi_nickname'  # 
    
    GSI_USER_NICKNAME_PK = 'nickname'  # u.nickname
    
    GSI_USER_NICKNAME_SK = 'sk'  # ["bn#<n.nft_id>","bc#<n.collection_id>"]
    
