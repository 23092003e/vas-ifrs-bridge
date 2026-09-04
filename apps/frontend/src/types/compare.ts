export interface StandardItem {
	code: string;
	name: string;
	category: string;
}

export interface RelationItem {
	topic: string;
	vas: string;
	ifrs: string;
	ias?: string;
	relationship: string;
	major_differences: string;
}

export interface TopicItem {
	topic_id: string;
	topic_name: string;
	aliases: string[];
	related_topics: string[];
}

export interface StandardsData {
	vas_standards: StandardItem[];
	ifrs_standards: StandardItem[];
	relations: RelationItem[];
	topics: TopicItem[];
}
