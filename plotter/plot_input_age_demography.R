library(ggplot2)
library(jsonlite)  # For parsing JSON
library(dplyr)     # For data manipulation
library(ggplot2)
library(XML)      # For parsing XML
library(dplyr)    # For data manipulation


age_input_emod <- function() {
  # The JSON chunk as a string
  json_data <- '{
    "AgeDistribution": {
        "DistributionValues": [
            [
                0, 0.0874071047257126, 0.16737703029028825, 0.24054255502934432,
                0.3074826208089575, 0.3686613109892203, 0.4246989953576121,
                0.47596861687986874, 0.522875857439861, 0.5657918836833704,
                0.6050561581209166, 0.6409789502300984, 0.673845189729804,
                0.7038827889943505, 0.7313967340232171, 0.7565694182395838,
                0.7795999267083209, 0.800670843446059, 0.8199488968312877,
                0.8375866300551988, 0.8537235049479931, 0.8684713425858462,
                0.8819801447631247, 0.8943395212968485, 0.9056472694733465,
                0.915992766949792, 0.9254579031519203, 0.9341176809019833,
                0.9420406227370048, 0.9492816775343581, 0.9559142701362873,
                0.9619824759265774, 0.9675343569769829, 0.9726138439176826,
                0.9772611297725079, 0.981512933676782, 0.9854029390818465,
                0.9889581498026758, 0.9922146658619191, 0.9951940927775798,
                0.9979199629370703, 1.0000000000000013, 1.0000000000000013,
                1.0000000000000013, 1.0000000000000013, 1.0000000000000013,
                1.0000000000000013, 1.0000000000000013, 1.0000000000000013,
                1.0000000000000013
            ]
        ],
        "ResultScaleFactor": 1,
        "ResultValues": [
            [
                0, 894, 1788, 2682, 3576, 4469, 5363, 6257, 7151, 8045, 8939,
                9833, 10727, 11620, 12514, 13408, 14302, 15196, 16090, 16984,
                17878, 18771, 19665, 20559, 21453, 22347, 23241, 24135, 25029,
                25922, 26816, 27710, 28604, 29498, 30392, 31286, 32180, 33073,
                33967, 34861, 35755, 36649, 37543, 38437, 39331, 40224, 41118,
                42012, 42906, 43800
            ]
        ]
    }
  }'

  # Parse the JSON data
  data <- fromJSON(json_data)
  distribution_values <- data$AgeDistribution$DistributionValues[[1]]
  result_values <- data$AgeDistribution$ResultValues[[1]]

  # Create a data frame for ggplot2
  df <- data.frame(Age = result_values, Distribution = distribution_values)

  # Create the bar plot
  p <- ggplot(df, aes(x = Age, y = Distribution)) +
    geom_bar(stat = "identity", fill = "skyblue") +
    labs(x = "Age in Days", y = "Distribution Percentage",
         title = "Age Distribution by Days") +
    theme_minimal()

  # Save the plot as a PNG
  ggsave("EMOD_age_input_cum.png", plot = p, width = 8, height = 6)
}


age_input_openmalaria <- function() {
  # The XML chunk as a string
  xml_data <- '<ageGroup lowerbound="0">
        <group poppercent="3.474714994" upperbound="1"/>
        <group poppercent="12.76004028" upperbound="5"/>
        <group poppercent="14.52151394" upperbound="10"/>
        <group poppercent="12.75565434" upperbound="15"/>
        <group poppercent="10.836323739" upperbound="20"/>
        <group poppercent="8.393312454" upperbound="25"/>
        <group poppercent="7.001421452" upperbound="30"/>
        <group poppercent="5.800587654" upperbound="35"/>
        <group poppercent="5.102136612" upperbound="40"/>
        <group poppercent="4.182561874" upperbound="45"/>
        <group poppercent="3.339409351" upperbound="50"/>
        <group poppercent="2.986112356" upperbound="55"/>
        <group poppercent="2.555766582" upperbound="60"/>
        <group poppercent="2.332763433" upperbound="65"/>
        <group poppercent="1.77400255" upperbound="70"/>
        <group poppercent="1.008525491" upperbound="75"/>
        <group poppercent="0.74167341" upperbound="80"/>
        <group poppercent="0.271863401" upperbound="85"/>
        <group poppercent="0.161614642" upperbound="90"/>
    </ageGroup>'

  # Parse the XML
  root <- xmlTreeParse(xml_data, asText = TRUE, useInternalNodes = TRUE)
  age_groups <- getNodeSet(root, "//group")

  # Extract the data into vectors
  upperbounds <- sapply(age_groups, function(x) as.numeric(xmlGetAttr(x, "upperbound")))
  poppercents <- sapply(age_groups, function(x) as.numeric(xmlGetAttr(x, "poppercent")))

  # Create a data frame for ggplot2
  df <- data.frame(AgeUpperBound = upperbounds, PopulationPercent = poppercents)

  # Bar Plot for Population Percentage by Age Group
  p1 <- ggplot(df, aes(x = AgeUpperBound, y = PopulationPercent)) +
    geom_bar(stat = "identity", fill = "skyblue") +
    labs(x = "Age Upper Bound", y = "Population Percentage",
         title = "Population Percentage by Age Group") +
    theme_minimal() +
    scale_x_continuous(breaks = upperbounds) +  # Ensure all age groups are labeled
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

  # Save the plot as a PNG
  ggsave("OpenMalaria_age_input.png", plot = p1, width = 8, height = 6)

  # Bar Plot for Cumulative Population Percentage
  df <- df %>%
    mutate(CumulativePercent = cumsum(PopulationPercent))

  p2 <- ggplot(df, aes(x = AgeUpperBound, y = CumulativePercent)) +
    geom_bar(stat = "identity", fill = "lightgreen") +
    labs(x = "Age Upper Bound", y = "Cumulative Population Percentage",
         title = "Cumulative Population Percentage by Age Group") +
    theme_minimal() +
    scale_x_continuous(breaks = upperbounds) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

  # Save the cumulative plot as a PNG
  ggsave("OpenMalaria_age_input_cum.png", plot = p2, width = 8, height = 6)
}


age_input_malariasimulation <- function() {

}


# Generate plots per model

age_input_emod()

age_input_malariasimulation()

age_input_openmalaria()





