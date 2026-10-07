# FIBO definition evidence

Repository revision: 9a7b90ccc64ef9df0762121ff058c9d27fd46037
Committed: 2026-10-01T18:30:45Z
Examined: 2026-10-06

These extracts support specific interpretation and reuse decisions. They do not establish that the integrated disclosure pattern is absent from all FIBO modules.

## FundClassification

Module: CollectiveInvestmentVehicles.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundClassification

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundClassification">
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/Classifiers/Classifier" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Classifiers/classifies" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Securities/Pools/CollectiveInvestmentVehicle" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label xml:lang="en">fund classification</ns2:label>
		<ns3:definition xml:lang="en">The category of the fund according to the asset class. This is a published code by which the Fund is classified. Further notes: Could be EFCF codes. This is the way in which "Type of fund" is articulated.</ns3:definition>
	</ns0:Class>
```

## FundClassificationScheme

Module: CollectiveInvestmentVehicles.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundClassificationScheme

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundClassificationScheme">
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/Classifiers/ClassificationScheme" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Designators/defines" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundClassification" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label xml:lang="en">fund classification scheme</ns2:label>
		<ns3:definition xml:lang="en">A published scheme for the category of a fund according to the asset class.</ns3:definition>
	</ns0:Class>
```

## FundPortfolioInvestmentLimitations

Module: CollectiveInvestmentVehicles.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentLimitations

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentLimitations">
		<ns2:subClassOf rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/InvestmentRestriction" />
		<ns2:label xml:lang="en">fund portfolio investment limitations</ns2:label>
		<ns3:definition xml:lang="en">Detailed Policy on approximately how the portfolio is to be allocated to achieve the stated investment goals. This underpins the detailed strategy of how to achieve this.</ns3:definition>
		<ns4:explanatoryNote xml:lang="en">Defined as "Strategy" in FIBIM and elsewhere. WG11: Rough allocation of the portfolio.</ns4:explanatoryNote>
	</ns0:Class>
```

## FundPortfolioInvestmentPolicy

Module: CollectiveInvestmentVehicles.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentPolicy

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentPolicy">
		<ns2:subClassOf rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/Law/LegalCapacity/Policy" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/definesAllocations" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentLimitations" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/RegulatoryAgencies/governs" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/PortfolioInvestmentStrategy" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label xml:lang="en">fund portfolio investment policy</ns2:label>
		<ns3:definition xml:lang="en">policy with respect to allocation of the portfolio that is designed to meet the stated investment strategy and goals</ns3:definition>
		<ns4:explanatoryNote xml:lang="en">ISO FIBIM: Rough allocation of the portfolio.</ns4:explanatoryNote>
	</ns0:Class>
```

## definesAllocations

Module: CollectiveInvestmentVehicles.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/definesAllocations

```xml
<ns0:ObjectProperty xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/definesAllocations">
		<ns2:subPropertyOf rdf:resource="https://www.omg.org/spec/Commons/Designators/defines" />
		<ns2:label xml:lang="en">defines allocations</ns2:label>
		<ns2:domain rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentPolicy" />
		<ns2:range rdf:resource="https://spec.edmcouncil.org/fibo/ontology/SEC/Funds/CollectiveInvestmentVehicles/FundPortfolioInvestmentLimitations" />
	</ns0:ObjectProperty>
```

## BasketConstituent

Module: FinancialProductsAndServices.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/BasketConstituent

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/BasketConstituent">
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/Collections/Constituent" />
		<ns2:label>basket constituent</ns2:label>
		<ns0:equivalentClass>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Collections/isConstituentOf" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/Basket" />
			</ns0:Restriction>
		</ns0:equivalentClass>
		<ns3:definition>component of a basket</ns3:definition>
	</ns0:Class>
```

## WeightedBasket

Module: FinancialProductsAndServices.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasket

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasket">
		<ns2:subClassOf rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/Basket" />
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/Collections/StructuredCollection" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Collections/hasMember" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasketConstituent" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/QuantitiesAndUnits/hasExpression" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/Utilities/Analytics/WeightingFunction" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label>weighted basket</ns2:label>
		<ns3:definition>basket whose constituents have some relative importance with respect to one another</ns3:definition>
	</ns0:Class>
```

## WeightedBasketConstituent

Module: FinancialProductsAndServices.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasketConstituent

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/WeightedBasketConstituent">
		<ns2:subClassOf rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/FinancialProductsAndServices/BasketConstituent" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/Utilities/Analytics/hasWeight" />
				<ns0:onDataRange rdf:resource="http://www.w3.org/2001/XMLSchema#decimal" />
				<ns0:qualifiedCardinality rdf:datatype="http://www.w3.org/2001/XMLSchema#nonNegativeInteger">1</ns0:qualifiedCardinality>
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label>weighted basket constituent</ns2:label>
		<ns3:definition>component of a basket whose relative importance with respect to other basket constituents is known</ns3:definition>
	</ns0:Class>
```

## hasAsOfDate

Module: FinancialDates.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FND/DatesAndTimes/FinancialDates/hasAsOfDate

```xml
<ns0:ObjectProperty xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FND/DatesAndTimes/FinancialDates/hasAsOfDate">
		<ns2:subPropertyOf rdf:resource="https://www.omg.org/spec/Commons/DatesAndTimes/hasDate" />
		<ns2:label>has as-of date</ns2:label>
		<ns3:definition>relates something to the date on which it is accurate or valid (e.g. a credit report has an asOfDate that means the date when the information was drawn)</ns3:definition>
		<ns4:explanatoryNote>It is different from the creation date and need not be the last date of the DatePeriod covered.</ns4:explanatoryNote>
	</ns0:ObjectProperty>
```

## Holding

Module: Ownership.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Holding

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Holding">
		<ns2:subClassOf rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Asset" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/Law/LegalCapacity/hasFractionalInterest" />
				<ns0:minQualifiedCardinality rdf:datatype="http://www.w3.org/2001/XMLSchema#nonNegativeInteger">0</ns0:minQualifiedCardinality>
				<ns0:onDataRange rdf:resource="http://www.w3.org/2001/XMLSchema#decimal" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label>holding</ns2:label>
		<ns3:definition>owned financial interest consisting of legal or beneficial ownership of an asset or security that confers economic rights on its owner</ns3:definition>
		<ns4:explanatoryNote>Note that there is no common, broadly accepted definition of the term holding across regulators, either within a single country such as the US, or across national jurisdictions. Typically, a holding may refer to a single asset, such as a piece of real estate, a portfolio of assets, multiple portfolios, and so forth, and may be aggregated over multiple assets.</ns4:explanatoryNote>
	</ns0:Class>
```

## Portfolio

Module: Ownership.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Portfolio

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Portfolio">
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/Collections/Collection" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Collections/isMemberOf" />
				<ns0:onClass rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Portfolio" />
				<ns0:maxQualifiedCardinality rdf:datatype="http://www.w3.org/2001/XMLSchema#nonNegativeInteger">1</ns0:maxQualifiedCardinality>
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/Collections/comprises" />
				<ns0:someValuesFrom rdf:resource="https://spec.edmcouncil.org/fibo/ontology/FND/OwnershipAndControl/Ownership/Holding" />
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label>portfolio</ns2:label>
		<ns3:definition>collection of holdings assembled and maintained as a unit for management purposes to achieve strategic objectives</ns3:definition>
		<ns4:adaptedFrom rdf:datatype="http://www.w3.org/2001/XMLSchema#anyURI">http://www.investopedia.com/terms/h/holdings.asp</ns4:adaptedFrom>
		<ns4:adaptedFrom rdf:datatype="http://www.w3.org/2001/XMLSchema#anyURI">http://www.investopedia.com/terms/p/portfolio.asp</ns4:adaptedFrom>
		<ns4:explanatoryNote>The holdings of any given portfolio may include a variety of investment products, including stocks, bonds and mutual funds to options, futures and exchange-traded funds, and relatively esoteric instruments such as private equity and hedge funds as well as other assets of the owner, such as interests in real estate, art, or vehicles. 

With respect to financial assets, the number and nature of holdings contribute to the degree of diversification of a portfolio. A mix of stocks across different sectors, bonds of different maturities, and other investments would suggest a well-diversified portfolio, while concentrated holdings in a handful of stocks within a single sector indicates a portfolio with limited diversification.</ns4:explanatoryNote>
	</ns0:Class>
```

## Publisher

Module: Publishers.rdf
IRI: https://spec.edmcouncil.org/fibo/ontology/BE/FunctionalEntities/Publishers/Publisher

```xml
<ns0:Class xmlns:ns0="http://www.w3.org/2002/07/owl#" xmlns:ns2="http://www.w3.org/2000/01/rdf-schema#" xmlns:ns3="http://www.w3.org/2004/02/skos/core#" xmlns:ns4="https://www.omg.org/spec/Commons/AnnotationVocabulary/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="https://spec.edmcouncil.org/fibo/ontology/BE/FunctionalEntities/Publishers/Publisher">
		<ns2:subClassOf rdf:resource="https://www.omg.org/spec/Commons/PartiesAndSituations/PartyRole" />
		<ns2:subClassOf>
			<ns0:Restriction>
				<ns0:onProperty rdf:resource="https://www.omg.org/spec/Commons/RolesAndCompositions/isPlayedBy" />
				<ns0:onClass rdf:resource="https://www.omg.org/spec/Commons/PartiesAndSituations/Party" />
				<ns0:minQualifiedCardinality rdf:datatype="http://www.w3.org/2001/XMLSchema#nonNegativeInteger">0</ns0:minQualifiedCardinality>
			</ns0:Restriction>
		</ns2:subClassOf>
		<ns2:label>publisher</ns2:label>
		<ns3:definition>role of person(s) or organization(s) responsible for the printing or distribution of an item, whether in digital or print (physical) form</ns3:definition>
		<ns4:adaptedFrom>ISO 10161-1:2014(en), Information and documentation - Open Systems Interconnection - Interlibrary Loan Application Protocol Specification - Part 1: Protocol specification</ns4:adaptedFrom>
		<ns4:explanatoryNote>Publishers may also include banks, government agencies and the like.</ns4:explanatoryNote>
	</ns0:Class>
```
